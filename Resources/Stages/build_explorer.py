import json, math, base64, pymupdf, xml.etree.ElementTree as E
from pathlib import Path
import numpy as np
B=Path(__file__).resolve().parent
summary=json.loads((B/'stage_summary.json').read_text())['stages']
stages=[]
for s in summary:
 p=E.parse(B/f'Stage_{s["stage"]}.gpx').findall('.//{*}trkpt')
 a=np.array([[float(t.attrib['lat']),float(t.attrib['lon']),float(t.find('{*}ele').text)] for t in p])
 q=np.radians(a[:,:2]);v=np.diff(q,axis=0)
 d=np.r_[0,np.cumsum(12742*np.arcsin(np.sqrt(np.sin(v[:,0]/2)**2+np.cos(q[:-1,0])*np.cos(q[1:,0])*np.sin(v[:,1]/2)**2)))]
 # 100 m visual sampling; original GPX remains embedded for exact download.
 ds=np.linspace(0,d[-1],int(d[-1]/.1)+2)
 arr=np.column_stack([ds,*[np.interp(ds,d,a[:,k]) for k in range(3)]])
 doc=pymupdf.open(B/f'Stage_{s["stage"]}_Official_Map.pdf')
 s['maps']=['data:image/jpeg;base64,'+base64.b64encode(page.get_pixmap(matrix=pymupdf.Matrix(1.4,1.4)).tobytes('jpeg')).decode() for page in doc]
 s['points']=np.round(arr,6).tolist();s['gpx']=(B/f'Stage_{s["stage"]}.gpx').read_text();stages.append(s)
html=(B/'explorer-template.html').read_text(encoding='utf-8').replace('__STAGE_DATA__',json.dumps(stages,separators=(',',':')))
# Written to the repo root for GitHub Pages: https://mashoedoe.github.io/Desert_Dash/stages.html
out=B.parent.parent/'stages.html'
out.write_text(html,encoding='utf-8')
print('Created',out,len(html),'characters')
