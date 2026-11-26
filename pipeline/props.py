"""Forward test: model player projections vs. posted prop markets. Log picks before games, grade after.

usage: python3 props.py log      (record picks for the props in NEW_PROPS)
       python3 props.py grade    (fill in results from nflverse weekly player stats)
"""
import json, os, sys, math
import numpy as np, pandas as pd
from scipy.stats import norm
import players as P

D = os.path.join(os.path.dirname(__file__), '..', 'data')
LOG = f'{D}/prop_log.json'
STAT_COL = {'pass_yds': 'passing_yards', 'rush_yds': 'rushing_yards', 'rec_yds': 'receiving_yards'}

# Pricing rules from Nov 25, 2026 ("v2"), after the first 152 graded props went 74-78:
# - P(over) comes from how often similar projections actually cleared the line in 2024-25 (data/prop_hist.csv), not a
#   bell curve: yardage is skewed, and the bell curve made the model too confident, mostly on NO picks.
# - The model's probability is blended 50/50 with Kalshi's price: on those 152 props the market's price was better
#   calibrated than the model, and the blend roughly matched it.
# - A pick is logged only if the blended probability beats the price paid (YES at the ask, NO at 1 - bid) by 5 cents,
#   and at most 4 per game (the biggest edges), so one game script can't swing a whole week. The rest are logged as PASS.
BLEND, MIN_EDGE, MAX_PER_GAME, RULES = 0.5, 0.05, 4, 'v2'
_HIST = None


def p_emp(stat, proj, thr, band=0.15, min_n=150):
    """P(stat >= thr) from historical games whose projection was within +/-15% of this one (widened until 150+ games),
    each scaled to this projection."""
    global _HIST
    if _HIST is None:
        _HIST = pd.read_csv(f'{D}/prop_hist.csv')
    h = _HIST[_HIST.stat == stat]
    x = h[(h.proj >= proj * (1 - band)) & (h.proj <= proj * (1 + band))]
    while len(x) < min_n and band < 0.6:
        band += 0.05
        x = h[(h.proj >= proj * (1 - band)) & (h.proj <= proj * (1 + band))]
    adj = x.act * (proj / x.proj.clip(lower=1))
    return float(((adj >= thr - 0.5).sum() + 1) / (len(adj) + 2))

# Kalshi "X+" markets for the Week 10 Sunday and Monday games (all but Patriots-Lions in Munich, whose pages would not load),
# from the Kalshi API between 12:15 and 12:45 PM ET on Nov 14, 2026. For each player, the threshold priced closest to 50% on the
# first page of each market list, kept when the midpoint is 35-65% and the spread is 10 cents or less. Kenneth Walker III and
# Emmett Johnson are left out because Walker's status was a coin flip; inactive markets (players ruled out) are left out too.
NEW_PROPS = [
    dict(game='2026_10_BUF_NYJ', player='Josh Allen', stat='pass_yds', thr=225, price=0.575, bid=0.56, ask=0.59),
    dict(game='2026_10_BUF_NYJ', player='Geno Smith', stat='pass_yds', thr=225, price=0.495, bid=0.49, ask=0.5),
    dict(game='2026_10_CAR_NO', player='Tyler Shough', stat='pass_yds', thr=250, price=0.525, bid=0.52, ask=0.53),
    dict(game='2026_10_CAR_NO', player='Bryce Young', stat='pass_yds', thr=250, price=0.495, bid=0.49, ask=0.5),
    dict(game='2026_10_KC_ATL', player='Patrick Mahomes', stat='pass_yds', thr=250, price=0.46, bid=0.45, ask=0.47),
    dict(game='2026_10_KC_ATL', player='Michael Penix Jr.', stat='pass_yds', thr=225, price=0.47, bid=0.45, ask=0.49),
    dict(game='2026_10_MIA_IND', player='Kyle McCord', stat='pass_yds', thr=150, price=0.57, bid=0.55, ask=0.59),
    dict(game='2026_10_MIA_IND', player='Daniel Jones', stat='pass_yds', thr=175, price=0.57, bid=0.55, ask=0.59),
    dict(game='2026_10_SEA_LV', player='Fernando Mendoza', stat='pass_yds', thr=175, price=0.555, bid=0.55, ask=0.56),
    dict(game='2026_10_PIT_CIN', player='Aaron Rodgers', stat='pass_yds', thr=250, price=0.455, bid=0.44, ask=0.47),
    dict(game='2026_10_PIT_CIN', player='Joe Burrow', stat='pass_yds', thr=300, price=0.465, bid=0.46, ask=0.47),
    dict(game='2026_10_LAC_BAL', player='Jacoby Brissett', stat='pass_yds', thr=225, price=0.44, bid=0.41, ask=0.47),
    dict(game='2026_10_LAC_BAL', player='Justin Herbert', stat='pass_yds', thr=200, price=0.525, bid=0.51, ask=0.54),
    dict(game='2026_10_LA_ARI', player='Matthew Stafford', stat='pass_yds', thr=200, price=0.575, bid=0.56, ask=0.59),
    dict(game='2026_10_LA_ARI', player='Carson Beck', stat='pass_yds', thr=175, price=0.535, bid=0.53, ask=0.54),
    dict(game='2026_10_HOU_CLE', player='C.J. Stroud', stat='pass_yds', thr=250, price=0.47, bid=0.46, ask=0.48),
    dict(game='2026_10_HOU_CLE', player='Deshaun Watson', stat='pass_yds', thr=200, price=0.575, bid=0.55, ask=0.6),
    dict(game='2026_10_MIN_GB', player='Jordan Love', stat='pass_yds', thr=250, price=0.535, bid=0.52, ask=0.55),
    dict(game='2026_10_SF_DAL', player='Brock Purdy', stat='pass_yds', thr=250, price=0.545, bid=0.53, ask=0.56),
    dict(game='2026_10_SF_DAL', player='Dak Prescott', stat='pass_yds', thr=275, price=0.495, bid=0.49, ask=0.5),
    dict(game='2026_10_JAX_TEN', player='Cam Ward', stat='pass_yds', thr=200, price=0.52, bid=0.5, ask=0.54),
    dict(game='2026_10_JAX_TEN', player='Trevor Lawrence', stat='pass_yds', thr=250, price=0.455, bid=0.44, ask=0.47),
    dict(game='2026_10_BUF_NYJ', player='James Cook III', stat='rush_yds', thr=90, price=0.51, bid=0.5, ask=0.52),
    dict(game='2026_10_BUF_NYJ', player='Braelon Allen', stat='rush_yds', thr=30, price=0.565, bid=0.55, ask=0.58),
    dict(game='2026_10_BUF_NYJ', player='Josh Allen', stat='rush_yds', thr=30, price=0.46, bid=0.45, ask=0.47),
    dict(game='2026_10_BUF_NYJ', player='Breece Hall', stat='rush_yds', thr=60, price=0.415, bid=0.4, ask=0.43),
    dict(game='2026_10_CAR_NO', player='Bryce Young', stat='rush_yds', thr=10, price=0.43, bid=0.42, ask=0.44),
    dict(game='2026_10_CAR_NO', player='Chuba Hubbard', stat='rush_yds', thr=80, price=0.495, bid=0.49, ask=0.5),
    dict(game='2026_10_CAR_NO', player='Tyler Shough', stat='rush_yds', thr=15, price=0.55, bid=0.54, ask=0.56),
    dict(game='2026_10_KC_ATL', player='Michael Penix Jr.', stat='rush_yds', thr=10, price=0.395, bid=0.39, ask=0.4),
    dict(game='2026_10_KC_ATL', player='Patrick Mahomes', stat='rush_yds', thr=10, price=0.47, bid=0.44, ask=0.5),
    dict(game='2026_10_KC_ATL', player='Bijan Robinson', stat='rush_yds', thr=80, price=0.555, bid=0.52, ask=0.59),
    dict(game='2026_10_KC_ATL', player='Khalil Herbert', stat='rush_yds', thr=10, price=0.485, bid=0.48, ask=0.49),
    dict(game='2026_10_MIA_IND', player='Ollie Gordon II', stat='rush_yds', thr=70, price=0.52, bid=0.51, ask=0.53),
    dict(game='2026_10_MIA_IND', player='Seth McGowan', stat='rush_yds', thr=25, price=0.475, bid=0.47, ask=0.48),
    dict(game='2026_10_MIA_IND', player='Jonathan Taylor', stat='rush_yds', thr=70, price=0.5, bid=0.49, ask=0.51),
    dict(game='2026_10_MIA_IND', player='Kyle McCord', stat='rush_yds', thr=10, price=0.39, bid=0.38, ask=0.4),
    dict(game='2026_10_MIA_IND', player='Daniel Jones', stat='rush_yds', thr=10, price=0.445, bid=0.42, ask=0.47),
    dict(game='2026_10_JAX_TEN', player='Bhayshul Tuten', stat='rush_yds', thr=60, price=0.515, bid=0.51, ask=0.52),
    dict(game='2026_10_JAX_TEN', player='Cam Ward', stat='rush_yds', thr=10, price=0.515, bid=0.51, ask=0.52),
    dict(game='2026_10_JAX_TEN', player='Trevor Lawrence', stat='rush_yds', thr=10, price=0.435, bid=0.42, ask=0.45),
    dict(game='2026_10_JAX_TEN', player='Tony Pollard', stat='rush_yds', thr=60, price=0.465, bid=0.45, ask=0.48),
    dict(game='2026_10_MIN_GB', player='Kaleb Johnson', stat='rush_yds', thr=30, price=0.465, bid=0.46, ask=0.47),
    dict(game='2026_10_MIN_GB', player='Pierre Strong Jr.', stat='rush_yds', thr=10, price=0.48, bid=0.44, ask=0.52),
    dict(game='2026_10_MIN_GB', player='Aaron Jones Sr.', stat='rush_yds', thr=25, price=0.56, bid=0.55, ask=0.57),
    dict(game='2026_10_MIN_GB', player='Jordan Mason', stat='rush_yds', thr=45, price=0.535, bid=0.52, ask=0.55),
    dict(game='2026_10_MIN_GB', player='MarShawn Lloyd', stat='rush_yds', thr=15, price=0.485, bid=0.48, ask=0.49),
    dict(game='2026_10_LA_ARI', player='Carson Beck', stat='rush_yds', thr=10, price=0.555, bid=0.55, ask=0.56),
    dict(game='2026_10_LA_ARI', player='Bam Knight', stat='rush_yds', thr=30, price=0.495, bid=0.49, ask=0.5),
    dict(game='2026_10_LA_ARI', player='Kyren Williams', stat='rush_yds', thr=60, price=0.56, bid=0.54, ask=0.58),
    dict(game='2026_10_LA_ARI', player='Blake Corum', stat='rush_yds', thr=60, price=0.485, bid=0.48, ask=0.49),
    dict(game='2026_10_LA_ARI', player='Tyler Allgeier', stat='rush_yds', thr=30, price=0.58, bid=0.57, ask=0.59),
    dict(game='2026_10_SEA_LV', player='Mike Washington Jr.', stat='rush_yds', thr=25, price=0.5, bid=0.47, ask=0.53),
    dict(game='2026_10_SEA_LV', player='Zach Charbonnet', stat='rush_yds', thr=60, price=0.525, bid=0.51, ask=0.54),
    dict(game='2026_10_SEA_LV', player='Jadarian Price', stat='rush_yds', thr=40, price=0.535, bid=0.51, ask=0.56),
    dict(game='2026_10_SEA_LV', player='Ashton Jeanty', stat='rush_yds', thr=30, price=0.55, bid=0.54, ask=0.56),
    dict(game='2026_10_SEA_LV', player='Fernando Mendoza', stat='rush_yds', thr=15, price=0.45, bid=0.44, ask=0.46),
    dict(game='2026_10_SF_DAL', player='Javonte Williams', stat='rush_yds', thr=65, price=0.495, bid=0.48, ask=0.51),
    dict(game='2026_10_SF_DAL', player='Dak Prescott', stat='rush_yds', thr=10, price=0.495, bid=0.49, ask=0.5),
    dict(game='2026_10_SF_DAL', player='Brock Purdy', stat='rush_yds', thr=15, price=0.61, bid=0.59, ask=0.63),
    dict(game='2026_10_SF_DAL', player='Kaelon Black', stat='rush_yds', thr=35, price=0.495, bid=0.49, ask=0.5),
    dict(game='2026_10_SF_DAL', player='Christian McCaffrey', stat='rush_yds', thr=60, price=0.525, bid=0.51, ask=0.54),
    dict(game='2026_10_PIT_CIN', player='Joe Burrow', stat='rush_yds', thr=10, price=0.39, bid=0.37, ask=0.41),
    dict(game='2026_10_PIT_CIN', player='Jaylen Warren', stat='rush_yds', thr=60, price=0.58, bid=0.57, ask=0.59),
    dict(game='2026_10_PIT_CIN', player='Chase Brown', stat='rush_yds', thr=40, price=0.58, bid=0.55, ask=0.61),
    dict(game='2026_10_PIT_CIN', player='Samaje Perine', stat='rush_yds', thr=20, price=0.48, bid=0.47, ask=0.49),
    dict(game='2026_10_PIT_CIN', player='Rico Dowdle', stat='rush_yds', thr=30, price=0.525, bid=0.5, ask=0.55),
    dict(game='2026_10_LAC_BAL', player='Derrick Henry', stat='rush_yds', thr=70, price=0.575, bid=0.56, ask=0.59),
    dict(game='2026_10_LAC_BAL', player='Kimani Vidal', stat='rush_yds', thr=20, price=0.48, bid=0.46, ask=0.5),
    dict(game='2026_10_LAC_BAL', player='Justice Hill', stat='rush_yds', thr=15, price=0.44, bid=0.43, ask=0.45),
    dict(game='2026_10_LAC_BAL', player='Omarion Hampton', stat='rush_yds', thr=25, price=0.62, bid=0.59, ask=0.65),
    dict(game='2026_10_LAC_BAL', player='Keaton Mitchell', stat='rush_yds', thr=15, price=0.365, bid=0.35, ask=0.38),
    dict(game='2026_10_LAC_BAL', player='Jacoby Brissett', stat='rush_yds', thr=10, price=0.375, bid=0.37, ask=0.38),
    dict(game='2026_10_LAC_BAL', player='Justin Herbert', stat='rush_yds', thr=20, price=0.52, bid=0.5, ask=0.54),
    dict(game='2026_10_HOU_CLE', player='Quinshon Judkins', stat='rush_yds', thr=40, price=0.55, bid=0.53, ask=0.57),
    dict(game='2026_10_HOU_CLE', player='Deshaun Watson', stat='rush_yds', thr=25, price=0.48, bid=0.47, ask=0.49),
    dict(game='2026_10_HOU_CLE', player='C.J. Stroud', stat='rush_yds', thr=10, price=0.455, bid=0.45, ask=0.46),
    dict(game='2026_10_HOU_CLE', player='Dylan Sampson', stat='rush_yds', thr=20, price=0.47, bid=0.46, ask=0.48),
    dict(game='2026_10_HOU_CLE', player='Woody Marks', stat='rush_yds', thr=60, price=0.455, bid=0.44, ask=0.47),
    dict(game='2026_10_BUF_NYJ', player='James Cook III', stat='rec_yds', thr=10, price=0.42, bid=0.4, ask=0.44),
    dict(game='2026_10_BUF_NYJ', player='Khalil Shakir', stat='rec_yds', thr=50, price=0.42, bid=0.4, ask=0.44),
    dict(game='2026_10_BUF_NYJ', player='Mason Taylor', stat='rec_yds', thr=10, price=0.645, bid=0.62, ask=0.67),
    dict(game='2026_10_BUF_NYJ', player='Kenyon Sadiq', stat='rec_yds', thr=20, price=0.535, bid=0.52, ask=0.55),
    dict(game='2026_10_BUF_NYJ', player='Ty Johnson', stat='rec_yds', thr=20, price=0.405, bid=0.38, ask=0.43),
    dict(game='2026_10_BUF_NYJ', player='Breece Hall', stat='rec_yds', thr=15, price=0.565, bid=0.55, ask=0.58),
    dict(game='2026_10_BUF_NYJ', player='Keon Coleman', stat='rec_yds', thr=20, price=0.61, bid=0.58, ask=0.64),
    dict(game='2026_10_BUF_NYJ', player='Omar Cooper Jr.', stat='rec_yds', thr=40, price=0.46, bid=0.43, ask=0.49),
    dict(game='2026_10_BUF_NYJ', player='DJ Moore', stat='rec_yds', thr=50, price=0.45, bid=0.43, ask=0.47),
    dict(game='2026_10_CAR_NO', player='Tetairoa McMillan', stat='rec_yds', thr=60, price=0.54, bid=0.52, ask=0.56),
    dict(game='2026_10_CAR_NO', player='Jordyn Tyson', stat='rec_yds', thr=50, price=0.395, bid=0.39, ask=0.4),
    dict(game='2026_10_CAR_NO', player='Juwan Johnson', stat='rec_yds', thr=25, price=0.505, bid=0.5, ask=0.51),
    dict(game='2026_10_CAR_NO', player='Devaughn Vele', stat='rec_yds', thr=25, price=0.57, bid=0.55, ask=0.59),
    dict(game='2026_10_CAR_NO', player='Tommy Tremble', stat='rec_yds', thr=15, price=0.505, bid=0.5, ask=0.51),
    dict(game='2026_10_CAR_NO', player='Chuba Hubbard', stat='rec_yds', thr=15, price=0.58, bid=0.57, ask=0.59),
    dict(game='2026_10_KC_ATL', player='Drake London', stat='rec_yds', thr=70, price=0.515, bid=0.51, ask=0.52),
    dict(game='2026_10_KC_ATL', player='Josh Downs', stat='rec_yds', thr=20, price=0.545, bid=0.53, ask=0.56),
    dict(game='2026_10_KC_ATL', player='Jahan Dotson', stat='rec_yds', thr=30, price=0.48, bid=0.46, ask=0.5),
    dict(game='2026_10_KC_ATL', player='Travis Kelce', stat='rec_yds', thr=50, price=0.495, bid=0.49, ask=0.5),
    dict(game='2026_10_KC_ATL', player='Xavier Worthy', stat='rec_yds', thr=25, price=0.53, bid=0.51, ask=0.55),
    dict(game='2026_10_MIA_IND', player='Deion Burks', stat='rec_yds', thr=15, price=0.555, bid=0.54, ask=0.57),
    dict(game='2026_10_MIA_IND', player='Anthony Gould', stat='rec_yds', thr=20, price=0.435, bid=0.42, ask=0.45),
    dict(game='2026_10_MIA_IND', player='Greg Dulcich', stat='rec_yds', thr=30, price=0.56, bid=0.54, ask=0.58),
    dict(game='2026_10_MIA_IND', player='Ollie Gordon II', stat='rec_yds', thr=10, price=0.375, bid=0.37, ask=0.38),
    dict(game='2026_10_MIA_IND', player='Ashton Dulin', stat='rec_yds', thr=15, price=0.515, bid=0.51, ask=0.52),
    dict(game='2026_10_HOU_CLE', player='Jerry Jeudy', stat='rec_yds', thr=25, price=0.36, bid=0.34, ask=0.38),
    dict(game='2026_10_HOU_CLE', player='Tank Dell', stat='rec_yds', thr=50, price=0.425, bid=0.42, ask=0.43),
    dict(game='2026_10_HOU_CLE', player='Woody Marks', stat='rec_yds', thr=10, price=0.525, bid=0.49, ask=0.56),
    dict(game='2026_10_HOU_CLE', player='Denzel Boston', stat='rec_yds', thr=40, price=0.56, bid=0.54, ask=0.58),
    dict(game='2026_10_HOU_CLE', player='Nico Collins', stat='rec_yds', thr=60, price=0.515, bid=0.51, ask=0.52),
    dict(game='2026_10_HOU_CLE', player='KC Concepcion', stat='rec_yds', thr=40, price=0.595, bid=0.57, ask=0.62),
    dict(game='2026_10_HOU_CLE', player='Dylan Sampson', stat='rec_yds', thr=30, price=0.37, bid=0.35, ask=0.39),
    dict(game='2026_10_JAX_TEN', player='Brian Thomas Jr.', stat='rec_yds', thr=10, price=0.49, bid=0.48, ask=0.5),
    dict(game='2026_10_JAX_TEN', player='Bhayshul Tuten', stat='rec_yds', thr=15, price=0.47, bid=0.46, ask=0.48),
    dict(game='2026_10_JAX_TEN', player='Chimere Dike', stat='rec_yds', thr=25, price=0.565, bid=0.55, ask=0.58),
    dict(game='2026_10_JAX_TEN', player='Elic Ayomanor', stat='rec_yds', thr=25, price=0.525, bid=0.51, ask=0.54),
    dict(game='2026_10_JAX_TEN', player='Travis Hunter', stat='rec_yds', thr=10, price=0.495, bid=0.49, ask=0.5),
    dict(game='2026_10_JAX_TEN', player='Jakobi Meyers', stat='rec_yds', thr=40, price=0.53, bid=0.52, ask=0.54),
    dict(game='2026_10_JAX_TEN', player='Parker Washington', stat='rec_yds', thr=70, price=0.435, bid=0.43, ask=0.44),
    dict(game='2026_10_JAX_TEN', player='Calvin Ridley', stat='rec_yds', thr=20, price=0.425, bid=0.41, ask=0.44),
    dict(game='2026_10_MIN_GB', player='Matthew Golden', stat='rec_yds', thr=70, price=0.5, bid=0.49, ask=0.51),
    dict(game='2026_10_MIN_GB', player='Aaron Jones Sr.', stat='rec_yds', thr=15, price=0.375, bid=0.37, ask=0.38),
    dict(game='2026_10_MIN_GB', player='Gavin Bartholomew', stat='rec_yds', thr=25, price=0.445, bid=0.43, ask=0.46),
    dict(game='2026_10_MIN_GB', player='Tucker Kraft', stat='rec_yds', thr=40, price=0.445, bid=0.44, ask=0.45),
    dict(game='2026_10_MIN_GB', player='Ben Yurosek', stat='rec_yds', thr=15, price=0.495, bid=0.48, ask=0.51),
    dict(game='2026_10_LA_ARI', player='Konata Mumpfield', stat='rec_yds', thr=30, price=0.515, bid=0.51, ask=0.52),
    dict(game='2026_10_LA_ARI', player='Trey McBride', stat='rec_yds', thr=70, price=0.38, bid=0.36, ask=0.4),
    dict(game='2026_10_LA_ARI', player='Tyler Higbee', stat='rec_yds', thr=40, price=0.445, bid=0.43, ask=0.46),
    dict(game='2026_10_LA_ARI', player='Blake Corum', stat='rec_yds', thr=10, price=0.395, bid=0.39, ask=0.4),
    dict(game='2026_10_LA_ARI', player='Colby Parkinson', stat='rec_yds', thr=30, price=0.535, bid=0.52, ask=0.55),
    dict(game='2026_10_LA_ARI', player='CJ Daniels', stat='rec_yds', thr=10, price=0.55, bid=0.54, ask=0.56),
    dict(game='2026_10_LA_ARI', player='Tutu Atwell', stat='rec_yds', thr=30, price=0.495, bid=0.49, ask=0.5),
    dict(game='2026_10_SEA_LV', player='Michael Mayer', stat='rec_yds', thr=15, price=0.63, bid=0.6, ask=0.66),
    dict(game='2026_10_SEA_LV', player='Ashton Jeanty', stat='rec_yds', thr=25, price=0.48, bid=0.46, ask=0.5),
    dict(game='2026_10_SEA_LV', player='Jaxon Smith-Njigba', stat='rec_yds', thr=90, price=0.5, bid=0.49, ask=0.51),
    dict(game='2026_10_SEA_LV', player='AJ Barner', stat='rec_yds', thr=25, price=0.43, bid=0.41, ask=0.45),
    dict(game='2026_10_SEA_LV', player='Tre Tucker', stat='rec_yds', thr=25, price=0.525, bid=0.51, ask=0.54),
    dict(game='2026_10_SEA_LV', player='Jalen Nailor', stat='rec_yds', thr=15, price=0.47, bid=0.46, ask=0.48),
    dict(game='2026_10_SF_DAL', player='Christian McCaffrey', stat='rec_yds', thr=30, price=0.56, bid=0.55, ask=0.57),
    dict(game='2026_10_SF_DAL', player='Keenan Allen', stat='rec_yds', thr=20, price=0.495, bid=0.48, ask=0.51),
    dict(game='2026_10_SF_DAL', player='CeeDee Lamb', stat='rec_yds', thr=90, price=0.495, bid=0.49, ask=0.5),
    dict(game='2026_10_SF_DAL', player='Jordan Watkins', stat='rec_yds', thr=30, price=0.4, bid=0.39, ask=0.41),
    dict(game='2026_10_SF_DAL', player='Ryan Flournoy', stat='rec_yds', thr=30, price=0.61, bid=0.58, ask=0.64),
    dict(game='2026_10_SF_DAL', player='Demarcus Robinson', stat='rec_yds', thr=40, price=0.365, bid=0.35, ask=0.38),
    dict(game='2026_10_PIT_CIN', player='Chase Brown', stat='rec_yds', thr=25, price=0.47, bid=0.46, ask=0.48),
    dict(game='2026_10_PIT_CIN', player='Germie Bernard', stat='rec_yds', thr=50, price=0.53, bid=0.52, ask=0.54),
    dict(game='2026_10_PIT_CIN', player='Mike Gesicki', stat='rec_yds', thr=25, price=0.495, bid=0.49, ask=0.5),
    dict(game='2026_10_PIT_CIN', player="Ja'Marr Chase", stat='rec_yds', thr=100, price=0.4, bid=0.38, ask=0.42),
    dict(game='2026_10_PIT_CIN', player='Darnell Washington', stat='rec_yds', thr=30, price=0.48, bid=0.46, ask=0.5),
    dict(game='2026_10_PIT_CIN', player='Rico Dowdle', stat='rec_yds', thr=15, price=0.465, bid=0.45, ask=0.48),
    dict(game='2026_10_PIT_CIN', player='Tee Higgins', stat='rec_yds', thr=80, price=0.46, bid=0.44, ask=0.48),
    dict(game='2026_10_PIT_CIN', player='Dohnte Meyers', stat='rec_yds', thr=20, price=0.51, bid=0.5, ask=0.52),
    dict(game='2026_10_PIT_CIN', player='Jaylen Warren', stat='rec_yds', thr=20, price=0.6, bid=0.58, ask=0.62),
    dict(game='2026_10_LAC_BAL', player='Zay Flowers', stat='rec_yds', thr=70, price=0.5, bid=0.49, ask=0.51),
    dict(game='2026_10_LAC_BAL', player='Kimani Vidal', stat='rec_yds', thr=10, price=0.455, bid=0.43, ask=0.48),
    dict(game='2026_10_LAC_BAL', player='Keaton Mitchell', stat='rec_yds', thr=10, price=0.52, bid=0.49, ask=0.55),
    dict(game='2026_10_LAC_BAL', player='Rashod Bateman', stat='rec_yds', thr=20, price=0.545, bid=0.5, ask=0.59),
    dict(game='2026_10_LAC_BAL', player='Mark Andrews', stat='rec_yds', thr=25, price=0.44, bid=0.42, ask=0.46),
    dict(game='2026_10_LAC_BAL', player='Justice Hill', stat='rec_yds', thr=15, price=0.405, bid=0.37, ask=0.44),
]
SOURCE = 'Kalshi API, Nov 14 12:30 PM ET'


def calibration():
    """From Weeks 4-9: actual = c + d*projection, and spread (sd) as a function of projection, per stat."""
    rows = []
    for wk in range(4, 10):
        H, lg, opp = P.build_context(wk)
        for p in P.W[P.W.week == wk].itertuples():
            hist = H[H.player_id == p.player_id]
            if len(hist) < 2: continue
            pr = P.project(p.player_id, p.team, p.opponent_team, H, lg, opp)
            if pr is None: continue
            if p.grp == 'QB' and hist.attempts.mean() >= 15 and p.attempts >= 10: rows.append(('pass_yds', pr['pass_yds'], p.passing_yards))
            if p.carries >= 1 or hist.carries.mean() >= 3: rows.append(('rush_yds', pr['rush_yds'], p.rushing_yards))
            if p.grp != 'QB' and hist.targets.mean() >= 2: rows.append(('rec_yds', pr['rec_yds'], p.receiving_yards))
    R = pd.DataFrame(rows, columns=['stat', 'proj', 'act'])
    cal = {}
    for st, g in R.groupby('stat'):
        d, c = np.polyfit(g.proj, g.act, 1)
        resid = g.act - (c + d * g.proj)
        g = g.assign(fit=c + d * g.proj, ares=resid.abs())
        s1, s0 = np.polyfit(g.fit, g.ares * math.sqrt(math.pi / 2), 1)  # mean abs residual -> sd
        cal[st] = {'c': float(c), 'd': float(d), 's0': float(s0), 's1': float(s1), 'n': int(len(g))}
    return cal


def prob_over(proj, thr, st, cal):
    k = cal[st]
    mu = k['c'] + k['d'] * proj
    sd = max(6.0, k['s0'] + k['s1'] * mu)
    return mu, sd, 1 - norm.cdf((thr - 0.5 - mu) / sd)


def log():
    proj = {(p['game'], p['name'], ): p for p in json.load(open(f'{D}/players.json'))['players']}
    entries = json.load(open(LOG)) if os.path.exists(LOG) else []
    have = {(e['game'], e['player'], e['stat'], e['thr']) for e in entries}
    for pr in NEW_PROPS:
        key = (pr['game'], pr['player'], pr['stat'], pr['thr'])
        if key in have: continue
        p = next((v for (g, n), v in proj.items() if g == pr['game'] and (n == pr['player'] or n.startswith(pr['player']))), None)
        raw = p.get(pr['stat']) if p else None
        if raw is None: print('no projection for', pr); continue
        pov = p_emp(pr['stat'], raw, pr['thr'])
        bid, ask = pr.get('bid', pr['price']), pr.get('ask', pr['price'])   # buy YES at the ask; buy NO at 1 - bid
        mid = (bid + ask) / 2
        conf_yes = BLEND * pov + (1 - BLEND) * mid
        side = 'YES' if conf_yes - ask > bid - conf_yes else 'NO'
        edge = (conf_yes - ask) if side == 'YES' else (bid - conf_yes)
        entries.append({**pr, 'source': SOURCE, 'raw_proj': round(raw, 1), 'proj': round(raw, 1), 'sd': None, 'p_over': round(pov, 3),
                        'conf': round(conf_yes if side == 'YES' else 1 - conf_yes, 3), 'side': side, 'pick': side, 'edge': round(edge, 3),
                        'rules': RULES, 'actual': None, 'won': None, 'profit': None, 'pid': p['id']})
    # only real edges, at most MAX_PER_GAME per game
    new = [e for e in entries if e.get('rules') == RULES and e['actual'] is None and e['pick'] != 'PASS']
    for g in {e['game'] for e in new}:
        ranked = sorted([e for e in new if e['game'] == g], key=lambda e: -e['edge'])
        for i, e in enumerate(ranked):
            if e['edge'] < MIN_EDGE or i >= MAX_PER_GAME:
                e['pick'] = 'PASS'
    json.dump(entries, open(LOG, 'w'), indent=1)
    return entries, {}


def grade(stats_csv=f'{D}/stats_player_week_2026.csv'):
    W = pd.read_csv(stats_csv, low_memory=False)
    entries = json.load(open(LOG))
    for e in entries:
        if e['actual'] is not None: continue
        wk = int(e['game'].split('_')[1])
        r = W[(W.player_id == e['pid']) & (W.week == wk)]
        if r.empty: continue
        a = float(r[STAT_COL[e['stat']]].iloc[0])
        over = a >= e['thr']
        e['actual'] = a
        if e['pick'] == 'PASS':   # tracked, not bet
            continue
        e['won'] = (over and e['pick'] == 'YES') or (not over and e['pick'] == 'NO')
        cost = e.get('ask', e['price']) if e['pick'] == 'YES' else 1 - e.get('bid', e['price'])
        e['profit'] = round((1 - cost) if e['won'] else -cost, 3)
    json.dump(entries, open(LOG, 'w'), indent=1)
    return entries


if __name__ == '__main__':
    if sys.argv[1:] == ['grade']:
        es = grade()
    else:
        es, cal = log()
    for e in es:
        print(f"{e['player']:18s} {e['stat']:8s} {e['thr']:>4}+  market {e['price']:.0%}  proj {e['proj']:6.1f}  P(over) {e['p_over']:.0%}  "
              f"pick {e['pick']:4s} conf {e.get('conf') or 0:.0%} edge {e['edge']:+.0%}  result {e['actual']}")
