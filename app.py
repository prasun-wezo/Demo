import time, hashlib, json, logging
from collections import defaultdict
from bs4 import BeautifulSoup
# import undetected_chromedriver as uc
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
import streamlit as st
import requests



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def hash_data(data):
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

def extract_match_data(soup):
    events = soup.select("div.event")
    matches = []
    for event in events:
        league_header = event.find_parent("article").find("h2")
        league = league_header.get_text(strip=True) if league_header else "Unknown"

        teams = event.select_one(".btmarket__link-name--2-rows")
        spans = teams.find_all("span") if teams else []
        home = spans[0].get_text(strip=True) if len(spans) > 0 else "N/A"
        away = spans[1].get_text(strip=True) if len(spans) > 1 else "N/A"

        live_scores = event.select(".btmarket__livescore-item")
        home_score = live_scores[0].text.strip() if len(live_scores) > 0 else "-"
        away_score = live_scores[1].text.strip() if len(live_scores) > 1 else "-"

        time_div = event.select_one("label.btmarket__live.area-livescore.event__status, .scoreboard__time, .event-header__time, .btmarket__header time")
        match_time = time_div.get_text(strip=True) if time_div else "N/A"

        more_bets_tag = event.select_one("btmarket__name.btmarket__more-bets-counter, a.btmarket__more-bets-counter")
        more_bets = more_bets_tag.text.strip() if more_bets_tag else "N/A"

        odds = {}
        for btn in event.select(".btmarket__selection button"):
            team = btn.get("data-name", "Unknown")
            val = btn.select_one(".betbutton__odds")
            odds[team] = val.text.strip() if val else "N/A"

        matches.append({
            "League": league,
            "Home Team": home,
            "Away Team": away,
            "Home Score": home_score,
            "Away Score": away_score,
            "Match Time": match_time,
            "Odds (Home)": odds.get(home, "N/A"),
            "Odds (Draw)": odds.get("Draw", "N/A"),
            "Odds (Away)": odds.get(away, "N/A"),
            "More Bets": more_bets,
        })
    return matches

# --- Streamlit App ---

st.set_page_config(layout="wide")
st.title("⚽ Football Live status")

placeholder = st.empty()

# Add blinking CSS
st.markdown("""
    <style>
    .blink {
        animation: blink-animation 1s steps(5, start) 2;
        -webkit-animation: blink-animation 1s steps(5, start) 2;
    }
    @keyframes blink-animation {
        to {
            visibility: hidden;
        }
    }
    @-webkit-keyframes blink-animation {
        to {
            visibility: hidden;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Global to store previous match state
previous_matches = {}

def display_matches(matches):
    global previous_matches

    grouped = defaultdict(list)
    for match in matches:
        grouped[match["League"]].append(match)

    with placeholder.container():
        for league, games in grouped.items():
            st.markdown(f"### 🏆 {league}")
            for match in games:
                match_id = f"{match['Home Team']} vs {match['Away Team']}"

                col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 3, 1, 1.2, 1.2, 1.2, 0.8])

                # Compare fields
                old = previous_matches.get(match_id, {})

                # Time
                with col1:
                    blink = "blink" if old.get('Match Time') != match['Match Time'] else ""
                    st.markdown(
                        f"<div class='{blink}' style='background-color:#021ff7;border-radius:4px;padding:5px 10px;width:fit-content;font-weight:bold'>{match['Match Time']}</div>",
                        unsafe_allow_html=True)

                # Match Names
                with col2:
                    st.markdown(f"**{match['Home Team']} v {match['Away Team']}**")

                # Score
                with col3:
                    blink = "blink" if old.get('Home Score') != match['Home Score'] or old.get('Away Score') != match['Away Score'] else ""
                    st.markdown(
                        f"<div class='{blink}' style='background-color:#021ff7;border-radius:4px;padding:5px 10px;width:fit-content;font-weight:bold;text-align:center'>{match['Home Score']} - {match['Away Score']}</div>",
                        unsafe_allow_html=True)

                # Odds Home
                blink = "blink" if old.get('Odds (Home)') != match['Odds (Home)'] else ""
                col4.markdown(f"<div class='{blink}'><b>{match['Odds (Home)']}</b></div>", unsafe_allow_html=True)

                # Odds Draw
                blink = "blink" if old.get('Odds (Draw)') != match['Odds (Draw)'] else ""
                col5.markdown(f"<div class='{blink}'><b>{match['Odds (Draw)']}</b></div>", unsafe_allow_html=True)

                # Odds Away
                blink = "blink" if old.get('Odds (Away)') != match['Odds (Away)'] else ""
                col6.markdown(f"<div class='{blink}'><b>{match['Odds (Away)']}</b></div>", unsafe_allow_html=True)

                # More Bets
                with col7:
                    blink = "blink" if old.get('More Bets') != match['More Bets'] else ""
                    st.markdown(
                        f"<span class='{blink}' style='color:#3366cc;font-weight:bold'>{match['More Bets']}</span>",
                        unsafe_allow_html=True)

                # Update previous match
                previous_matches[match_id] = match

def start_scraper(url, interval=1):
    # options = uc.ChromeOptions()
    # options.headless = True
    # options.add_argument("--no-sandbox")
    # options.add_argument("--disable-gpu")
    # driver = uc.Chrome(options=options)
    # driver.get(url)
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.text, "html.parser")
    matches = extract_match_data(soup)
    display_matches(matches)

    last_hash = ""

    # try:
    #     while True:
    #         try:
    #             WebDriverWait(driver, 1).until(
    #                 EC.presence_of_element_located((By.CSS_SELECTOR, "div.sport-events-container"))
    #             )
    #             soup = BeautifulSoup(driver.page_source, "html.parser")
    #             matches = extract_match_data(soup)
    #             current_hash = hash_data(matches)

    #             if current_hash != last_hash:
    #                 display_matches(matches)
    #                 last_hash = current_hash
    #                 logging.info("🔄 UI updated.")
    #             else:
    #                 logging.info("⏳ No changes.")
    #         except Exception as e:
    #             st.warning(f"⚠️ Scrape error: {e}")
    #             logging.warning(f"⚠️ Scrape error: {e}")

    #         time.sleep(interval)

    # finally:
    #     driver.quit()
    while True:
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.text, "html.parser")
            matches = extract_match_data(soup)
            current_hash = hash_data(matches)

            if current_hash != last_hash:
                display_matches(matches)
                last_hash = current_hash
                logging.info("🔄 UI updated.")
            else:
                logging.info("⏳ No changes.")
        except Exception as e:
            st.warning(f"⚠️ Scrape error: {e}")
            logging.warning(f"⚠️ Scrape error: {e}")

        time.sleep(interval)

# Start scraper
start_scraper("https://sports.williamhill.com/betting/en-gb/in-play/all", interval=1)
