import os
import html5lib
from flask import Flask, request, render_template
from bs4 import BeautifulSoup as bsoup
import datetime
from collections import namedtuple
import requests
from pytz import timezone

app = Flask(__name__)

GAME_URL = (
	"http://www.nba.com/games/{year}{month}{day}/"
	"{away.shortcode}{home.shortcode}/gameinfo.html"
)

GAMELINE_URL = (
	"http://www.nba.com/gameline/{year}{month}{day}/"
)

Division = namedtuple("Division", ["name", "teams"])
Team = namedtuple("Team", ["name", "shortcode", "subreddit", "espn_url"])
Performance = namedtuple("Performance", ["name", "mins", "fg", "tre", "ft",
	"pm", "reb", "ast", "pf", "stl", "to", "blk", "pts"])
DNPPerformance  = namedtuple("DNPPerformance", ["name", "dnp"])

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
	doc = requests.get(GAME_URL.format(
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
		return DNPPerformance(tds[0].string, tds[1].string.split("-")[0])

	name = tds[0].string
	mins = tds[2].string
	fg = tds[3].string
	tre = tds[4].string
	ft = tds[5].string
	pm = tds[6].string
	reb = tds[9].string
	ast = tds[10].string
	pf = tds[11].string
	stl = tds[12].string
	to = tds[13].string
	blk = tds[14].string
	pts = tds[16].string

	return Performance(name, mins, fg, tre, ft, pm, reb, ast,
				pf, stl, to, blk, pts)

def get_performances(box):
	trs = box.find_all("tr")
	return [get_performance(tr) for i, tr in enumerate(trs) if i > 2 and i < len(trs) - 1]


def get_points_by_quarter(doc):
	quarter_points = {"home": [], "away": []}
	trs = doc.find(id="nbaGIQtrScrs").find_all("tr")
	quarter_points["home"] = [int(tr.string) for tr in trs[2].find_all("td")]
	quarter_points["home"].append(sum(quarter_points["home"]))
	quarter_points["away"] = [int(tr.string) for tr in trs[0].find_all("td")]
	quarter_points["away"].append(sum(quarter_points["away"]))

	return quarter_points


def generate_post_game(time, home, away, home_perfs, away_perfs, by_quarter):
	home_box = home_perfs.pop()
	away_box = away_perfs.pop()
	return render_template("postgame.txt",
									time=time, away=away, home=home,
									away_perfs=away_perfs, home_perfs=home_perfs,
									away_box=away_box, home_box=home_box,
									by_quarter=by_quarter)


def game_status(doc):
	time = doc.find("div", id="nbaGITmeQtr")

	if time is None:
		time = doc.find("p", class_="nbaGITime")
		time = time.get_text().split("-")[0].strip()
	else:
		old = time
		time = old.h2.get_text()
		if time != "HALF":
			print time
			time += " " + old.p.get_text()

	if "Q" in time or time == "HALF":
		return time

	return "Final" if "Final" in time else "Not Started"


def post_game(home, away, date):
	doc = get_game_html(home, away, date)

	if "Not Found" in doc.title.string:
		return "Bad URL"

	status = game_status(doc)

	if status == "Not Started":
		return status

	stats = doc.find_all(id="nbaGITeamStats")
	away_perfs = get_performances(stats[0])
	home_perfs = get_performances(stats[1])
	by_quarter = get_points_by_quarter(doc)

	return generate_post_game(status, home, away, home_perfs, away_perfs, by_quarter)


@app.route("/generate")
def generate():
	args = request.args

	year = int(args.get("year"))
	month = int(args.get("month"))
	day = int(args.get("day"))
	home = get_team(args.get("home"))
	away = get_team(args.get("away"))

	return post_game(home, away, datetime.date(year, month, day))

def get_game(div):
	away = div.find("div", class_="nbaPreMnStatusTeamAw")
	home = div.find("div", class_="nbaPreMnStatusTeamHm")
	gametime = div.find("div", class_="nbaLiveStatTxSm")

	print gametime

	if away is None:
		away = div.find("div", class_="nbaModTopTeamAw")
	if home is None:
		home = div.find("div", class_="nbaModTopTeamHm")
	if gametime is None:
		gametime = div.find("h2", class_="nbaFnlStatTx").get_text()
	elif gametime.get_text() == "":
		gametime = div.find("div", class_="nbaFnlStatTxSm").get_text()

	return {"home": get_team(home.get_text().upper()[:3]),
					"away": get_team(away.get_text().upper()[:3]),
					"time": gametime}


def get_todays_games(date):
	games = []
	doc = bsoup(requests.get(GAMELINE_URL.format(
		year=date.year,
		month=str(date.month).zfill(2),
		day=str(date.day).zfill(2),
	)).text)

	divs = doc.find(id="nbaSSOuter").find_all("div", class_="nbaModTopScore")

	return [get_game(g) for g in divs]

@app.route("/")
def home():
	dt = datetime.datetime.now(timezone("US/Pacific"))
	games = get_todays_games(dt)

	return render_template("index.html", date=dt, games=games)


if __name__ == "__main__":
	app.run(debug=True)
