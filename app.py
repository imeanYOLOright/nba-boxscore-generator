import os
import html5lib
from flask import Flask, render_template
from bs4 import BeautifulSoup as bsoup
import datetime
from collections import namedtuple
import requests
from pytz import timezone

app = Flask(__name__)

NBA_URL = (
	"http://www.nba.com/games/{year}{month}{day}/"
	"{away.shortcode}{home.shortcode}/gameinfo.html"
)

Division = namedtuple("Division", ["name", "teams"])
Team = namedtuple("Team", ["name", "shortcode", "subreddit", "espn_url"])
Performance = namedtuple("Performance", ["player", "min", "fg", "tre", "ft",
	"pm", "reb", "ast", "pf", "st", "to", "blk", "pts"])
DNPPerformance  = namedtuple("DNPPerformance", ["player", "dnp"])

DIVISIONS = [
    Division("Atlantic", [
        Team(
            "Boston Celtics", "BOS", "bostonceltics",
            "http://espn.go.com/nba/team/_/name/bos/boston-celtics",
        ),
        Team(
            "Brooklyn Nets", "BKN", "GoNets",
            "http://espn.go.com/nba/team/_/name/bkn/brooklyn-nets",
        ),
        Team(
            "New York Knicks", "NYK", "NYKnicks",
            "http://espn.go.com/nba/team/_/name/ny/new-york-knicks",
        ),
        Team(
            "Philadelphia 76ers", "PHI", "sixers",
            "http://espn.go.com/nba/team/_/name/phi/philadelphia-76ers",
        ),
        Team(
            "Toronto Raptors", "TOR", "torontoraptors",
            "http://espn.go.com/nba/team/_/name/tor/toronto-raptors"
        ),
    ]),
    Division("Central", [
        Team(
            "Chicago Bulls", "CHI", "chicagobulls",
            "http://espn.go.com/nba/team/_/name/chi/chicago-bulls"
        ),
        Team(
            "Cleveland Cavaliers", "CLE", "clevelandcavs",
            "http://espn.go.com/nba/team/_/name/cle/cleveland-cavaliers"
        ),
        Team(
            "Detroit Pistons", "DET", "DetroitPistons",
            "http://espn.go.com/nba/team/_/name/det/detroit-pistons"
        ),
        Team(
            "Indiana Pacers", "IND", "IndianaPacers",
            "http://espn.go.com/nba/team/_/name/ind/indiana-pacers"
        ),
        Team(
            "Milwaukee Bucks", "MIL", "mkebucks",
            "http://espn.go.com/nba/team/_/name/mil/milwaukee-bucks"
        ),
    ]),
    Division("Southeast", [
        Team(
            "Atlanta Hawks", "ATL", "AtlantaHawks",
            "http://espn.go.com/nba/team/_/name/atl/atlanta-hawks"
        ),
        Team(
            "Charlotte Bobcats", "CHA", "CharlotteBobcats",
            "http://espn.go.com/nba/team/_/name/cha/charlotte-bobcats"
        ),
        Team(
            "Miami Heat", "MIA", "heat",
            "http://espn.go.com/nba/team/_/name/mia/miami-heat"
        ),
        Team(
            "Orlando Magic", "ORL", "orlandomagic",
            "http://espn.go.com/nba/team/_/name/orl/orlando-magic"
        ),
        Team(
            "Washington Wizards", "WAS", "washingtonwizards",
            "http://espn.go.com/nba/team/_/name/wsh/washington-wizards"
        ),
    ]),
    Division("Pacific", [
        Team(
            "Golden State Warriors", "GSW", "warriors",
            "http://espn.go.com/nba/team/_/name/gs/golden-state-warriors"
        ),
        Team(
            "Los Angeles Clippers", "LAC", "LAClippers",
            "http://espn.go.com/nba/team/_/name/lac/los-angeles-clippers"
        ),
        Team(
            "Los Angeles Lakers", "LAL", "lakers",
            "http://espn.go.com/nba/team/_/name/lal/los-angeles-lakers"
        ),
        Team(
            "Phoenix Suns", "PHX", "SUNS",
            "http://espn.go.com/nba/team/_/name/phx/phoenix-suns"
        ),
        Team(
            "Sacramento Kings", "SAC", "kings",
            "http://espn.go.com/nba/team/_/name/sac/sacramento-kings"
        ),
    ]),
    Division("Southwest", [
        Team(
            "Dallas Mavericks", "DAL", "Mavericks",
            "http://espn.go.com/nba/team/_/name/dal/dallas-mavericks"
        ),
        Team(
            "Houston Rockets", "HOU", "rockets",
            "http://espn.go.com/nba/team/_/name/hou/houston-rockets"
        ),
        Team(
            "Memphis Grizzlies", "MEM", "memphisgrizzlies",
            "http://espn.go.com/nba/team/_/name/mem/memphis-grizzlies"
        ),
        Team(
            "New Orleans Pelicans", "NOP", "NOLAPelicans",
            "http://espn.go.com/nba/team/_/name/no/new-orleans-hornets"
        ),
        Team(
            "San Antonio Spurs", "SAS", "NBASpurs",
            "http://espn.go.com/nba/team/_/name/sa/san-antonio-spurs"
        ),
    ]),
    Division("Northwest", [
        Team(
            "Denver Nuggets", "DEN", "denvernuggets",
            "http://espn.go.com/nba/team/_/name/den/denver-nuggets"
        ),
        Team(
            "Minnesota Timberwolves", "MIN", "timberwolves",
            "http://espn.go.com/nba/team/_/name/min/minnesota-timberwolves"
        ),
        Team(
            "Oklahoma City Thunder", "OKC", "Thunder",
            "http://espn.go.com/nba/team/_/name/okc/oklahoma-city-thunder"
        ),
        Team(
            "Portland Trail Blazers", "POR", "ripcity",
            "http://espn.go.com/nba/team/_/name/por/portland-trail-blazers"
        ),
        Team(
            "Utah Jazz", "UTA", "UtahJazz",
            "http://espn.go.com/nba/team/_/name/utah/utah-jazz"
        ),
    ]),
]


def get_team(shortcode):
    for div in DIVISIONS:
        for team in div.teams:
            if team.shortcode == shortcode:
                return team
    raise LookupError


def get_game_html(home, away, date):
	doc = requests.get(NBA_URL.format(
		year=date.year,
		month=str(date.month).zfill(2),
		day=str(date.day).zfill(2),
		away=away,
		home=home,
	))
	return bsoup(doc.text)


def get_performance(row):
	tds = row.find_all("td")

	if len(tds) < 17:
		return DNPPerformance(tds[0].string, tds[1].string)

	name = tds[0].string
	mins = tds[2].string
	fg = tds[3].string
	tre = tds[4].string
	ft = tds[5].string
	pm = tds[6].string
	reb = tds[9].string
	ast = tds[10].string
	pf = tds[11].string
	st = tds[12].string
	to = tds[13].string
	blk = tds[14].string
	pts = tds[15].string

	return Performance(name, mins, fg, tre, ft, pm, reb, ast,
				pf, st, to, blk, pts)

def get_performances(box):
	trs = box.find_all("tr")
	return [get_performance(tr) for i, tr in enumerate(trs) if i > 1 and i < len(trs) - 1]


def get_points_by_quarter(doc):
	quarter_points = {"home": [], "away": []}
	trs = doc.find(id="nbaGIQtrScrs").find_all("tr")
	quarter_points["home"] = [int(tr.string) for tr in trs[0].find_all("td")]
	quarter_points["away"] = [int(tr.string) for tr in trs[2].find_all("td")]
	quarter_points["home"].append(sum(quarter_points["home"]))
	quarter_points["away"].append(sum(quarter_points["away"]))

	return quarter_points


def generate_post_game(home, away, home_perfs, away_perfs, by_quarter):
	home_box = home_perfs.pop()
	away_box = away_perfs.pop()
	return render_template("postgame.txt", away=away, home=home,
									away_box=away_box, home_box=home_box, by_quarter=by_quarter)


def post_game(home, away, date):
	doc = get_game_html(home, away, date)

	if "Not Found" in doc.title.string:
		return "Bad URL"

	stats = doc.find_all(id="nbaGITeamStats")
	away_perfs = get_performances(stats[0])
	home_perfs = get_performances(stats[1])
	by_quarter = get_points_by_quarter(doc)

	return generate_post_game(home, away, home_perfs, away_perfs, by_quarter)


@app.route("/")
def home():
	home = get_team("IND")
	away = get_team("ATL")
	pg = post_game(home, away, datetime.date(2014, 4, 6))#datetime.now(timezone("US/Pacific")))
	return pg

def execute(environ, response):
	app.run(debug=True)

if __name__ == "__main__":
	app.run(debug=True)
