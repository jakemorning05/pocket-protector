"""Aggregate nflverse play-by-play into one row per team per game (offense view), 2016-2026.

Output: data/teamgames.pkl  and  data/qb_games.pkl
"""
import pandas as pd, numpy as np, glob, os

D = os.path.join(os.path.dirname(__file__), '..', 'data')
FIX = {'SD': 'LAC', 'OAK': 'LV', 'STL': 'LA', 'LAR': 'LA'}
COLS = ['game_id', 'season', 'week', 'season_type', 'posteam', 'defteam', 'home_team', 'away_team', 'play_type',
        'pass', 'rush', 'qb_dropback', 'qb_scramble', 'qb_kneel', 'qb_spike', 'epa', 'success', 'wp', 'yards_gained',
        'interception', 'fumble_lost', 'fumble', 'sack', 'down', 'half_seconds_remaining', 'special_teams_play',
        'id', 'name', 'cpoe', 'air_yards', 'pass_oe', 'yardline_100', 'fixed_drive', 'touchdown', 'qtr']


def load(season):
    df = pd.read_csv(f'{D}/play_by_play_{season}.csv.gz', usecols=COLS, low_memory=False)
    df = df[df.season_type == 'REG']
    for c in ['posteam', 'defteam', 'home_team', 'away_team']:
        df[c] = df[c].replace(FIX)
    return df


def team_games(df):
    sc = df[((df['pass'] == 1) | (df['rush'] == 1)) & df.epa.notna() & (df.qb_kneel != 1) & (df.qb_spike != 1) & df.posteam.notna()].copy()
    sc['isdrop'] = (sc.qb_dropback == 1)
    sc['designed_run'] = (sc.rush == 1) & (sc.qb_scramble != 1)
    sc['early'] = sc.down.isin([1, 2])
    sc['neutral'] = sc.wp.between(0.2, 0.8) & (sc.half_seconds_remaining > 120)
    sc['explosive'] = (sc.isdrop & (sc.yards_gained >= 20)) | (sc.designed_run & (sc.yards_gained >= 10))
    sc['pass_epa_v'] = sc.epa.where(sc.isdrop); sc['rush_epa_v'] = sc.epa.where(sc.designed_run)
    sc['early_epa_v'] = sc.epa.where(sc.early); sc['neutral_epa_v'] = sc.epa.where(sc.neutral)
    sc['to'] = sc.interception.fillna(0) + sc.fumble_lost.fillna(0)
    sc['rz'] = sc.yardline_100 <= 20
    g = sc.groupby(['game_id', 'posteam'])
    out = pd.DataFrame({
        'plays': g.size(),
        'epa': g.epa.mean(),
        'sr': g.success.mean(),
        'ypp': g.yards_gained.mean(),
        'pass_epa': g.pass_epa_v.mean(),
        'rush_epa': g.rush_epa_v.mean(),
        'early_epa': g.early_epa_v.mean(),
        'neutral_epa': g.neutral_epa_v.mean(),
        'neutral_plays': g.neutral.sum(),
        'dropbacks': g['isdrop'].sum(),
        'explosive': g.explosive.mean(),
        'turnovers': g['to'].sum(),
        'fumbles': g.fumble.sum(),
        'fumbles_lost': g.fumble_lost.sum(),
        'ints': g.interception.sum(),
        'sacks': g.sack.sum(),
        'pass_oe': g.pass_oe.mean(),
        'cpoe': g.cpoe.mean(),
        'rz_plays': g.rz.sum(),
    }).reset_index().rename(columns={'posteam': 'team'})
    # red zone touchdown rate per drive that reached the 20
    rzd = sc[sc.rz].groupby(['game_id', 'posteam', 'fixed_drive']).touchdown.max().reset_index()
    rz = rzd.groupby(['game_id', 'posteam']).agg(rz_drives=('touchdown', 'size'), rz_tds=('touchdown', 'sum')).reset_index().rename(columns={'posteam': 'team'})
    out = out.merge(rz, on=['game_id', 'team'], how='left').fillna({'rz_drives': 0, 'rz_tds': 0})
    # special teams EPA: plays where team is posteam add epa, where it is defteam subtract
    st = df[(df.special_teams_play == 1) & df.epa.notna()]
    a = st.groupby(['game_id', 'posteam']).epa.sum().rename('st_for')
    b = st.groupby(['game_id', 'defteam']).epa.sum().rename('st_against')
    a.index.names = ['game_id', 'team']; b.index.names = ['game_id', 'team']
    stt = pd.concat([a, b], axis=1).fillna(0)
    stt['st_epa'] = stt.st_for - stt.st_against
    out = out.merge(stt[['st_epa']].reset_index(), on=['game_id', 'team'], how='left').fillna({'st_epa': 0})
    meta = df.groupby('game_id').agg(season=('season', 'first'), week=('week', 'first'), home_team=('home_team', 'first'), away_team=('away_team', 'first')).reset_index()
    out = out.merge(meta, on='game_id')
    out['home'] = (out.team == out.home_team).astype(int)
    out['opp'] = np.where(out.home == 1, out.away_team, out.home_team)
    return out


def qb_games(df):
    """Dropback EPA per QB per game (passes, sacks, scrambles)."""
    q = df[(df.qb_dropback == 1) & df.epa.notna() & df.id.notna() & (df.qb_spike != 1)]
    g = q.groupby(['game_id', 'season', 'week', 'posteam', 'id']).agg(name=('name', 'first'), db=('epa', 'size'), epa=('epa', 'sum'), cpoe=('cpoe', 'mean')).reset_index()
    return g.rename(columns={'posteam': 'team', 'id': 'qb_id'})


if __name__ == '__main__':
    tgs, qbs = [], []
    for s in range(2016, 2027):
        df = load(s)
        tgs.append(team_games(df)); qbs.append(qb_games(df))
        print(s, df.game_id.nunique(), 'games')
    tg = pd.concat(tgs, ignore_index=True); qb = pd.concat(qbs, ignore_index=True)
    tg.to_pickle(f'{D}/teamgames.pkl'); qb.to_pickle(f'{D}/qb_games.pkl')
    print(tg.shape, qb.shape)
    print(tg[tg.season == 2026].groupby('team')[['epa', 'sr', 'pass_epa', 'rush_epa', 'st_epa']].mean().sort_values('epa', ascending=False).round(3).head(8))
