from pathlib import Path
import copy, json, zipfile, xml.etree.ElementTree as ET
import numpy as np
from html import escape
import pymupdf

BASE = Path(__file__).resolve().parent
OUT = BASE / 'Stages'
OUT.mkdir(exist_ok=True)
ns = 'http://www.topografix.com/GPX/1/1'
ET.register_namespace('', ns)
root = ET.fromstring(zipfile.ZipFile(BASE/'2024_Full_Dash.zip').read('2024_Full_Dash.gpx'))
pts = root.findall('.//{*}trkpt')
a = np.array([[float(p.attrib['lat']), float(p.attrib['lon']), float(p.find('{*}ele').text)] for p in pts])
q = np.radians(a[:, :2]); delta = np.diff(q, axis=0)
dist = np.r_[0, np.cumsum(12742*np.arcsin(np.sqrt(np.sin(delta[:,0]/2)**2 + np.cos(q[:-1,0])*np.cos(q[1:,0])*np.sin(delta[:,1]/2)**2)))]
checkpoints = [(-(23+1/60+29.95/3600),16+20/60+37.01/3600), (-(23+3/60+27.86/3600),15+43/60+0.17/3600), (-(22+55/60+51.90/3600),15+18/60+35.05/3600), (-(22+40/60+6.16/3600),14+48/60+57.46/3600)]
indices = [0]; offsets = []
for lat, lon in checkpoints:
    ds = np.hypot((a[:,0]-lat)*111.195, (a[:,1]-lon)*111.195*np.cos(np.radians(lat)))
    ix = int(ds.argmin()); indices.append(ix); offsets.append(float(ds[ix]*1000))
indices.append(len(pts)-1)
assert all(x<y for x,y in zip(indices,indices[1:]))
names = ['Grove Mall', 'CP1 - Kuiseb / Superspar', 'CP2 - Hollard', 'CP3 - Bloedkoppe', 'CP4 - Goanikontes', 'Finish - Platz am Meer']
records=[]
combined=pymupdf.open()
for s,(lo,hi) in enumerate(zip(indices,indices[1:]),1):
        b=a[lo:hi+1]; d=dist[lo:hi+1]-dist[lo]
        sample=np.linspace(0,d[-1],max(2,int(d[-1]/.1)+1))
        z=np.interp(sample,d,b[:,2]); dz=np.diff(z)
        gain=float(dz[dz>0].sum()); loss=float(-dz[dz<0].sum())
        parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="800"><rect width="1120" height="800" fill="white"/>']
        def text(x,y,t,size=15,color='#333333'):
            parts.append(f'<text x="{x}" y="{y}" font-family="Arial" font-size="{size}" fill="{color}">{escape(str(t))}</text>')
        text(55,45,f'STAGE {s} | {names[s-1]} to {names[s]}',24,'#164f46')
        text(55,80,f'{d[-1]:.1f} km | Ascent ~{gain:,.0f} m | Descent ~{loss:,.0f} m | Race km {dist[lo]:.1f}-{dist[hi]:.1f}',18)
        text(55,113,'GPS route map | North up | No road basemap',14)
        x=b[:,1]*np.cos(np.radians(b[:,0].mean()))*111.195; y=b[:,0]*111.195
        scale=min(900/max(np.ptp(x),.01),240/max(np.ptp(y),.01))
        xx=560+(x-(x.max()+x.min())/2)*scale; yy=260-(y-(y.max()+y.min())/2)*scale
        path=' '.join(f'{i:.2f},{j:.2f}' for i,j in zip(xx,yy))
        parts.append(f'<polyline points="{path}" fill="none" stroke="#167365" stroke-width="2"/>')
        for ix,label in [(0,'START'),(-1,'FINISH')]:
            parts.append(f'<circle cx="{xx[ix]}" cy="{yy[ix]}" r="5" fill="#bd752d"/>')
            text(xx[ix]+9,yy[ix]-8,label,12)
        text(1010,160,'N',18);text(1010,185,'^',24)
        text(55,424,'Elevation profile | Original GPX elevations (m)',16)
        zmin=max(0,np.floor(b[:,2].min()/100)*100-50); zmax=np.ceil(b[:,2].max()/100)*100+50
        xp=90+d/d[-1]*960;yp=660-(b[:,2]-zmin)/(zmax-zmin)*195
        for tick in np.linspace(zmin,zmax,5):
            ty=660-(tick-zmin)/(zmax-zmin)*195
            parts.append(f'<path d="M90 {ty} H1050" stroke="#dddddd"/>');text(35,ty+5,f'{tick:.0f}',12)
        for tick in np.linspace(0,d[-1],6):
            tx=90+tick/d[-1]*960;text(tx-10,681,f'{tick:.1f}',12)
        path=' '.join(f'{i:.2f},{j:.2f}' for i,j in zip(xp,yp))
        parts.append(f'<polyline points="{path}" fill="none" stroke="#167365" stroke-width="1.5"/>')
        text(410,706,'Distance from stage start (km)',14)
        text(55,741,'2024 GPX + 2025 checkpoint coordinates. Nearest-point splits; checkpoint offsets 3-89 m.',12)
        text(55,761,'Ascent/descent: ~100 m sampling. Independent profile scales. Elevation uncorrected; not a verified 2026 route.',12)
        parts.append('</svg>');svg=''.join(parts)
        (OUT/f'Stage_{s}_Map_and_Profile.svg').write_text(svg,encoding='utf-8')
        drawing=pymupdf.open(stream=svg.encode(),filetype='svg');sheet=pymupdf.open('pdf',drawing.convert_to_pdf())
        combined.insert_pdf(sheet)
        sheet[0].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).save(OUT/f'Stage_{s}_Map_and_Profile.png')
        g=ET.Element(f'{{{ns}}}gpx',{'version':'1.1','creator':'DesertDash stage split'})
        t=ET.SubElement(g,f'{{{ns}}}trk');ET.SubElement(t,f'{{{ns}}}name').text=f'Stage {s}: {names[s-1]} to {names[s]}'
        seg=ET.SubElement(t,f'{{{ns}}}trkseg')
        for p in pts[lo:hi+1]:seg.append(copy.deepcopy(p))
        ET.ElementTree(g).write(OUT/f'Stage_{s}.gpx',encoding='utf-8',xml_declaration=True)
        records.append(dict(stage=s,start=names[s-1],finish=names[s],distance_km=float(d[-1]),ascent_m=gain,descent_m=loss,start_index=lo,end_index=hi))
combined.save(OUT/'Desert_Dash_Stage_Maps_and_Profiles.pdf')
maps=pymupdf.open(BASE/'Maps-2025.pdf')
for s,pages in enumerate([[2],[3],[4],[5],[6,7]],1):
    out=pymupdf.open()
    for page in pages:out.insert_pdf(maps,from_page=page,to_page=page)
    out.save(OUT/f'Stage_{s}_Official_Map.pdf')
(OUT/'stage_summary.json').write_text(json.dumps({'checkpoint_offsets_m':offsets,'stages':records},indent=2))
(OUT/'README.md').write_text('''# Desert Dash stage resources

Open Desert_Dash_Stage_Maps_and_Profiles.pdf for all five GPS route maps and elevation profiles. Individual PNG sheets, split GPX tracks, and original official map pages are also included.

The full GPX contains 22,368 track points, all with elevation, in one track segment with no checkpoint waypoints. The supplied filename identifies it as 2024. Checkpoint coordinates were transcribed from the 2025 official maps and matched to the nearest track points. Offsets are approximately 3, 3, 30 and 89 metres. Adjacent stages share their boundary point; all original track points and elevations are preserved.

Distances are cumulative spherical great-circle distances (Earth radius 6,371 km); the total is approximately 400.0 km. Printed map distances differ and are internally inconsistent in places, so the splits use coordinates rather than printed kilometre totals. These are planning resources from the supplied historical files, not confirmed 2026 course files.

Elevation profiles use the original GPX elevations without external terrain correction. Their vertical datum and accuracy are unspecified. Ascent and descent are approximate, calculated after interpolation onto roughly 100 m distance intervals to reduce point-to-point noise. Each profile uses its own vertical range; compare numeric labels rather than visual steepness. GPS maps are north-up with longitude scaled by cosine of mean latitude; official schematic road maps are supplied separately.

Sources: ../2024_Full_Dash.zip and ../Maps-2025.pdf (checkpoint coordinates on PDF pages 3-6; official stage maps on pages 3-8). Website: https://desertdashnamibia.com/the-route/
''',encoding='utf-8')
print(json.dumps(records,indent=2))
doc=pymupdf.open(OUT/'Desert_Dash_Stage_Maps_and_Profiles.pdf')
for i,page in enumerate(doc):page.get_pixmap(matrix=pymupdf.Matrix(.8,.8)).save(BASE.parent/'tmp'/'pdfs'/f'stage-qa-{i+1}.png')
