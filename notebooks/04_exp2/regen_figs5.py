import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

import rmllm

PROJ = Path(rmllm.config.PROJ_ROOT)
DATA = PROJ / 'data' / 'processed'
SUP  = PROJ / 'reports' / 'figures' / 'supplemental'
SUP.mkdir(parents=True, exist_ok=True)

DPI_MANUSCRIPT = 700

plt.rcParams.update({
    'font.family': 'sans-serif', 'font.size': 11,
    'axes.titlesize': 11, 'axes.titleweight': 'bold',
    'axes.labelsize': 10, 'axes.labelweight': 'bold',
    'xtick.labelsize': 9,  'ytick.labelsize': 9,
    'axes.linewidth': 1.0, 'axes.facecolor': 'white',
    'figure.facecolor': 'white', 'axes.grid': False,
    'xtick.bottom': True, 'ytick.left': True,
    'xtick.direction': 'out', 'ytick.direction': 'out',
    'xtick.major.size': 4, 'ytick.major.size': 4,
    'legend.fontsize': 8.5, 'legend.framealpha': 0.9,
    'legend.edgecolor': '#cccccc',
})

MODEL_ORDER  = ['Gemma3:12b','Gemma3:12b-QAT','Gemma3:27b',
                'Gemma3:27b-QAT','Llama3.3:70b','Llama4:16x17b']
MODEL_LABELS = ['G3:12b','G3:12b\nQAT','G3:27b',
                'G3:27b\nQAT','L3.3:70b','L4:16x17b']
N_MDL = len(MODEL_ORDER)
x     = np.arange(N_MDL)

FB_LABEL= {True: 'Feedback', False: 'No Feedback'}
SRC_PAL = {'test:perceived': '#2166ac', 'test:imagined': '#d6604d'}
SRC_LABEL = {'test:perceived': 'External', 'test:imagined': 'Internal'}
SOURCES = ['test:imagined', 'test:perceived']

def _xticks(ax):
    ax.set_xticks(x)
    ax.set_xticklabels(MODEL_LABELS, fontsize=8.5, fontweight='bold',
                       rotation=40, ha='right', rotation_mode='anchor')
    ax.set_xlim(-0.6, N_MDL - 0.4)

# ── Load & preprocess data ─────────────────────────────────────────────
df = pd.read_csv(DATA / 'exp2_trial_data.csv')
df['model']               = df['model'].astype(str).str.strip()
df['source_test']         = df['source_test'].astype(str).str.strip()
df['setsize']             = df['setsize'].astype(int)
df['fb_exp']              = df['fb_exp'].astype(bool)
df['rating']              = pd.to_numeric(df['rating'], errors='coerce')

print("rows:", len(df), "rating non-null:", df['rating'].notna().sum())

# ── FigS5: Relatedness ratings — per-trace, then across traces ──────────
rr_trace = (df.groupby(['trace','model','source_test','setsize','fb_exp'], observed=True)['rating']
              .mean().reset_index())
rr = (rr_trace.groupby(['model','source_test','setsize','fb_exp'], observed=True)['rating']
               .agg(['mean','sem']).reset_index())
rr.columns = ['model','source_test','setsize','fb_exp','rr_mean','rr_sem']

print(rr.head(10))

fig, axes = plt.subplots(2, 2, figsize=(14, 9), sharey=True)

for ri, ss in enumerate([20, 40]):
    for ci, fb in enumerate([False, True]):
        ax = axes[ri, ci]
        sub = rr[(rr['setsize']==ss) & (rr['fb_exp']==fb)]
        for src in SOURCES:
            s = sub[sub['source_test']==src].set_index('model').reindex(MODEL_ORDER)
            ax.errorbar(x, s['rr_mean'].values, yerr=s['rr_sem'].values,
                        color=SRC_PAL[src], lw=2.0, marker='o', ms=5,
                        capsize=3, alpha=0.9, label=SRC_LABEL[src])
        _xticks(ax)
        ax.set_ylabel('Relatedness Rating (Mean ± SEM)')
        ax.set_title(f'Set-size {ss} · {FB_LABEL[fb]}',
                     fontsize=10, fontweight='bold')
        if ri==0 and ci==0:
            ax.legend(title='Source')

plt.tight_layout()
for fmt, dpi in [('pdf', DPI_MANUSCRIPT), ('png', DPI_MANUSCRIPT)]:
    fig.savefig(SUP / f'FigS5_exp2_relatedness.{fmt}', dpi=dpi, bbox_inches='tight')
print('FigS5 saved')
plt.close('all')
print('done')
