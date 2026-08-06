import fs from 'fs/promises';
import shapefile from 'shapefile';

(async function(){
  const props = JSON.parse(await fs.readFile('data/processed/Cambridge_Property_Database_FY2016-FY2026_20260805_deduped.geojson','utf8'));
  const propIds = new Set(props.features.map(f=> (f.properties.gisid||f.properties.map_lot||'').toString().trim()).filter(Boolean));
  const bSrc = await shapefile.open('data/raw/BASEMAP_Buildings.shp/BASEMAP_Buildings.shp');
  const bIds = new Set();
  while(true){
    const r = await bSrc.read();
    if (r.done) break;
    const bid = r.value && r.value.properties && (r.value.properties.BldgID || r.value.properties.BLDGID || r.value.properties.buildingid || r.value.properties.BLDG_ID);
    if (bid) bIds.add(String(bid).trim());
  }
  const intersection = [...propIds].filter(x=>bIds.has(x));
  console.log('property ids count:', propIds.size);
  console.log('building ids count:', bIds.size);
  console.log('intersection count:', intersection.length);
  console.log('intersection sample:', intersection.slice(0,20));
})();
