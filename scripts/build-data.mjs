#!/usr/bin/env node
import fs from 'fs/promises';
import path from 'path';

const repoRoot = process.cwd();

const propsPath = path.join(repoRoot, 'data/processed/Cambridge_Property_Database_FY2016-FY2026_20260805_deduped.geojson');
const ageBandsPath = path.join(repoRoot, 'data/processed/Age_bands.json');
const addressPointsPath = path.join(repoRoot, 'cambridgegis_data/Address/Address_Points/ADDRESS_AddressPoints.geojson');
const buildingsPath = path.join(repoRoot, 'cambridgegis_data/Basemap/Buildings/BASEMAP_Buildings.geojson');
const outPath = path.join(repoRoot, 'public/data/cambridge-buildings.geojson');

function normalizeId(v) {
  if (v === undefined || v === null) return '';
  let s = String(v);
  s = s.trim();
  if (s.endsWith('.0')) s = s.slice(0, -2);
  s = s.toUpperCase();
  return s;
}

function findKey(props, test) {
  if (!props) return null;
  const keys = Object.keys(props);
  for (const k of keys) {
    if (test(k)) return k;
  }
  return null;
}

function extractStreetNumber(addr) {
  if (!addr) return Number.POSITIVE_INFINITY;
  const m = String(addr).trim().match(/^0*(\d+)/);
  if (!m) return Number.POSITIVE_INFINITY;
  return parseInt(m[1], 10);
}

function chooseLowestAddress(addresses) {
  if (!addresses || addresses.length === 0) return null;
  const uniques = Array.from(new Set(addresses.filter(Boolean)));
  if (uniques.length === 0) return null;
  const withNum = uniques.map(a => ({ addr: a, num: extractStreetNumber(a) }));
  withNum.sort((a, b) => {
    if (a.num === b.num) return a.addr.localeCompare(b.addr);
    return a.num - b.num;
  });
  return withNum[0].addr;
}

function assignAgeBand(bands, year) {
  if (year === null || year === undefined || Number.isNaN(year)) return 'unknown';
  for (const b of bands) {
    const min = b.minYear;
    const max = b.maxYear;
    if ((min === null || min === undefined || year >= min) && (max === null || max === undefined || year <= max)) {
      return b.id || b.label || 'unknown';
    }
  }
  return 'unknown';
}

function buildAddressPointIndex(points) {
  const index = new Map();
  for (const pt of points) {
    if (!pt || !pt.properties) continue;
    const ml = normalizeId(pt.properties.ml || pt.properties.ML);
    if (!ml) continue;
    if (!index.has(ml)) index.set(ml, []);
    index.get(ml).push(pt);
  }
  return index;
}

function buildBuildingIndex(buildings) {
  const index = new Map();
  for (const b of buildings) {
    if (!b || !b.properties) continue;
    const id = normalizeId(b.properties.BldgID || b.properties.BLDGID || b.properties.bldgID);
    if (!id) continue;
    index.set(id, b);
  }
  return index;
}

function getAddressKey(props) {
  const candidates = ['dedupe_selected_address', 'dedupe_selected', 'address', 'addr', 'Full_Addr'];
  for (const key of candidates) {
    if (Object.prototype.hasOwnProperty.call(props, key)) return key;
  }
  return findKey(props, k => /address|addr/i.test(k));
}

async function main() {
  try {
    await fs.access(propsPath).catch(() => { throw new Error(`Missing file: ${propsPath}`); });
    await fs.access(ageBandsPath).catch(() => { throw new Error(`Missing file: ${ageBandsPath}`); });
    await fs.access(addressPointsPath).catch(() => { throw new Error(`Missing file: ${addressPointsPath}`); });
    await fs.access(buildingsPath).catch(() => { throw new Error(`Missing file: ${buildingsPath}`); });

    const [propsText, ageBandsText, addressPointsText, buildingsText] = await Promise.all([
      fs.readFile(propsPath, 'utf8'),
      fs.readFile(ageBandsPath, 'utf8'),
      fs.readFile(addressPointsPath, 'utf8'),
      fs.readFile(buildingsPath, 'utf8')
    ]);

    const propsGeo = JSON.parse(propsText);
    const ageBands = JSON.parse(ageBandsText);
    const addressPointsGeo = JSON.parse(addressPointsText);
    const buildingsGeo = JSON.parse(buildingsText);

    if (!propsGeo || propsGeo.type !== 'FeatureCollection' || !Array.isArray(propsGeo.features)) {
      throw new Error(`Expected a GeoJSON FeatureCollection at ${propsPath}`);
    }
    if (!addressPointsGeo || addressPointsGeo.type !== 'FeatureCollection' || !Array.isArray(addressPointsGeo.features)) {
      throw new Error(`Expected a GeoJSON FeatureCollection at ${addressPointsPath}`);
    }
    if (!buildingsGeo || buildingsGeo.type !== 'FeatureCollection' || !Array.isArray(buildingsGeo.features)) {
      throw new Error(`Expected a GeoJSON FeatureCollection at ${buildingsPath}`);
    }

    const propFeatures = propsGeo.features;
    const pointFeatures = addressPointsGeo.features;
    const buildingFeatures = buildingsGeo.features;

    const sampleProps = propFeatures.find(f => f && f.properties) ? propFeatures.find(f => f && f.properties).properties : {};
    const yearKey = findKey(sampleProps, k => /condition.*year|yearofbuilt|year[_ ]?built|condition_yearbuilt/i.test(k));
    const addrKey = getAddressKey(sampleProps);
    const propGisKey = findKey(sampleProps, k => /gisid|map[_ ]?lot|maplot|gis_id/i.test(k));

    if (!yearKey) throw new Error(`Missing expected year field (e.g. condition_YearBuilt) in properties of ${propsPath}`);
    if (!addrKey) throw new Error(`Missing expected address field (dedupe_selected_address or address) in properties of ${propsPath}`);
    if (!propGisKey) throw new Error(`Missing expected GISID field in properties of ${propsPath}`);

    const addressPointsByML = buildAddressPointIndex(pointFeatures);
    const buildingsByBldgID = buildBuildingIndex(buildingFeatures);
    if (buildingsByBldgID.size === 0) {
      throw new Error(`No buildings with BldgID found in ${buildingsPath}`);
    }

    const currentYear = new Date().getFullYear();
    const stats = {
      total: buildingFeatures.length,
      matched: 0,
      unmatched: 0,
      invalid_year: 0,
      ambiguous: 0,
      ageBandCounts: {}
    };
    for (const b of ageBands) stats.ageBandCounts[b.id || b.label || 'unknown'] = 0;

    const buildingMatches = new Map();
    const outFeatures = [];

    for (const prop of propFeatures) {
      if (!prop || !prop.properties) continue;
      const propProps = prop.properties;
      const propGisRaw = propProps[propGisKey];
      const masterML = normalizeId(propGisRaw);
      if (!masterML) continue;

      const pointGroup = addressPointsByML.get(masterML) || [];
      if (pointGroup.length === 0) continue;

      const pointAddresses = pointGroup.map(pt => pt.properties && pt.properties.Full_Addr).filter(Boolean);
      const pointBldgIDs = pointGroup.map(pt => normalizeId(pt.properties && pt.properties.BldgID)).filter(Boolean);
      const uniqueBldgIDs = Array.from(new Set(pointBldgIDs)).filter(Boolean);
      const joinAmbiguous = uniqueBldgIDs.length > 1;

      let chosenPoint = null;
      const canonicalBldgID = uniqueBldgIDs.length ? uniqueBldgIDs[0] : null;
      const candidates = canonicalBldgID
        ? pointGroup.filter(pt => normalizeId(pt.properties && pt.properties.BldgID) === canonicalBldgID)
        : pointGroup;
      const chosenAddr = chooseLowestAddress(candidates.map(pt => pt.properties && pt.properties.Full_Addr).filter(Boolean));
      if (chosenAddr) {
        chosenPoint = candidates.find(pt => String(pt.properties && pt.properties.Full_Addr).trim() === String(chosenAddr).trim());
      }
      if (!chosenPoint && candidates.length > 0) {
        chosenPoint = candidates[0];
      }

      const bldgRaw = chosenPoint && chosenPoint.properties && chosenPoint.properties.BldgID;
      const bldgID = normalizeId(bldgRaw);
      if (!bldgID) continue;

      if (!buildingsByBldgID.has(bldgID)) continue;
      if (!buildingMatches.has(bldgID)) buildingMatches.set(bldgID, []);
      buildingMatches.get(bldgID).push({ prop, joinAmbiguous });
    }

    for (const building of buildingFeatures) {
      const bProps = building.properties || {};
      const bldgID = normalizeId(bProps.BldgID || bProps.BLDGID || bProps.bldgID);
      const matches = (bldgID && buildingMatches.get(bldgID)) || [];
      const join_ambiguous = matches.some(m => m.joinAmbiguous) || matches.length > 1;
      let chosenProp = null;
      let chosenAddress = null;
      if (matches.length > 0) {
        const addresses = matches.map(m => m.prop.properties[addrKey]).filter(Boolean);
        chosenAddress = chooseLowestAddress(addresses);
        if (chosenAddress) {
          chosenProp = matches.find(m => String(m.prop.properties[addrKey]).trim() === String(chosenAddress).trim())?.prop;
        }
        if (!chosenProp) {
          chosenProp = matches[0].prop;
          chosenAddress = chosenProp.properties[addrKey];
        }
      }

      let Condition_YearBuilt = null;
      let PropertyClass = null;
      let Zoning = null;
      let age = null;
      let age_band = 'unknown';
      let join_status = 'unmatched';
      let GISID = null;

      if (matches.length === 0) {
        join_status = 'unmatched';
        stats.unmatched += 1;
      } else if (chosenProp && chosenProp.properties) {
        const rawYear = chosenProp.properties[yearKey];
        const cleaned = String(rawYear === undefined || rawYear === null ? '' : rawYear).trim().replace(/\.0$/, '');
        const yearNum = parseInt(cleaned.replace(/[^0-9-]/g, ''), 10);
        if (!rawYear || !Number.isFinite(yearNum) || yearNum < 1600 || yearNum > currentYear) {
          join_status = 'invalid_year';
          stats.invalid_year += 1;
        } else {
          Condition_YearBuilt = yearNum;
          age = currentYear - yearNum;
          age_band = assignAgeBand(ageBands, yearNum);
          join_status = 'matched';
          stats.matched += 1;
          stats.ageBandCounts[age_band] = (stats.ageBandCounts[age_band] || 0) + 1;
        }
        PropertyClass = chosenProp.properties.PropertyClass || chosenProp.properties.propertyclass || null;
        Zoning = chosenProp.properties.Zoning || chosenProp.properties.zoning || null;
        GISID = normalizeId(chosenProp.properties[propGisKey]);
      } else {
        join_status = 'unmatched';
        stats.unmatched += 1;
      }

      if (join_ambiguous) stats.ambiguous += 1;

      const outProps = {
        GISID,
        Address: chosenAddress || null,
        Condition_YearBuilt: Condition_YearBuilt === null ? null : Condition_YearBuilt,
        PropertyClass: PropertyClass || null,
        Zoning: Zoning || null,
        age: age === null ? null : age,
        age_band: age_band,
        join_status,
        join_ambiguous: !!join_ambiguous
      };

      outFeatures.push({ type: 'Feature', geometry: building.geometry, properties: outProps });
    }

    await fs.mkdir(path.dirname(outPath), { recursive: true });
    const outGeo = { type: 'FeatureCollection', features: outFeatures };
    await fs.writeFile(outPath, JSON.stringify(outGeo, null, 2), 'utf8');

    const total = stats.total;
    const matched = stats.matched;
    const unmatched = stats.unmatched;
    const invalid_year = stats.invalid_year;
    const ambiguous = stats.ambiguous;
    const matchPct = total === 0 ? 0 : (matched / total) * 100;
    const validYearCoveragePct = total === 0 ? 0 : (matched / total) * 100;

    console.log(`Total GeoJSON features: ${total}`);
    console.log(`Matched features: ${matched}`);
    console.log(`Unmatched features: ${unmatched}`);
    console.log(`Invalid-year features: ${invalid_year}`);
    console.log(`Ambiguous matches: ${ambiguous}`);
    console.log(`Match percentage: ${matchPct.toFixed(2)}%`);
    console.log(`Valid-year coverage percentage: ${validYearCoveragePct.toFixed(2)}%`);
    console.log('Count by age band:');
    for (const [band, cnt] of Object.entries(stats.ageBandCounts)) {
      console.log(`  ${band}: ${cnt}`);
    }
    console.log(`Wrote ${outPath}`);
  } catch (err) {
    console.error('Error:', err.message || err);
    process.exit(1);
  }
}

main();
