from flask import Flask, send_file, request, render_template, Response
import requests
import json
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import os
import re
from io import BytesIO
from config import ROBOTEVENTS_API_KEY

app = Flask(__name__)

def create_match_image(matches, output):
    # Grid layout settings - keeping same dimensions
    matches_per_row = 2
    padding = 50
    line_height = 45
    match_width = 600
    match_height = 350
    margin = 30
    team_spacing = 220
    
    # Calculate grid dimensions
    num_matches = len(matches)
    num_rows = (num_matches + matches_per_row - 1) // matches_per_row
    
    # Calculate total image size
    width = padding * 2 + match_width * matches_per_row + margin * (matches_per_row - 1)
    height = padding * 2 + match_height * num_rows + margin * (num_rows - 1)
    
    # Create image with white background
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    try:
        # Linux-specific font paths
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Primary choice
            "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",  # Alternative path
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Regular DejaVu
            "/usr/share/fonts/TTF/DejaVuSans.ttf"  # Another common path
        ]
        
        font_path = None
        for path in font_paths:
            if os.path.exists(path):
                font_path = path
                print(f"Using font: {font_path}")
                break
        
        if font_path:
            title_font = ImageFont.truetype(font_path, size=42)
            header_font = ImageFont.truetype(font_path, size=32)
            font = ImageFont.truetype(font_path, size=28)
        else:
            print("No system fonts found, falling back to default")
            title_font = ImageFont.load_default()
            header_font = title_font
            font = title_font
    except Exception as e:
        print(f"Font loading error: {str(e)}")
        title_font = ImageFont.load_default()
        header_font = title_font
        font = title_font

    # Draw title
    title = "Match Schedule"
    draw.text((padding, padding//2), title, fill=(60, 60, 60), font=title_font)
    
    def draw_rounded_rectangle(x, y, w, h, radius, color, outline=None):
        """Draw a rounded rectangle with proper corners"""
        # Draw the main rectangles
        draw.rectangle((x + radius, y, x + w - radius, y + h), fill=color)
        draw.rectangle((x, y + radius, x + w, y + h - radius), fill=color)
        
        # Draw the four corner circles
        draw.pieslice((x, y, x + radius * 2, y + radius * 2), 180, 270, fill=color)
        draw.pieslice((x + w - radius * 2, y, x + w, y + radius * 2), 270, 360, fill=color)
        draw.pieslice((x, y + h - radius * 2, x + radius * 2, y + h), 90, 180, fill=color)
        draw.pieslice((x + w - radius * 2, y + h - radius * 2, x + w, y + h), 0, 90, fill=color)
        
        if outline:
            draw.arc((x, y, x + radius * 2, y + radius * 2), 180, 270, fill=outline)
            draw.arc((x + w - radius * 2, y, x + w, y + radius * 2), 270, 360, fill=outline)
            draw.arc((x, y + h - radius * 2, x + radius * 2, y + h), 90, 180, fill=outline)
            draw.arc((x + w - radius * 2, y + h - radius * 2, x + w, y + h), 0, 90, fill=outline)
            draw.line((x + radius, y, x + w - radius, y), fill=outline)
            draw.line((x + radius, y + h, x + w - radius, y + h), fill=outline)
            draw.line((x, y + radius, x, y + h - radius), fill=outline)
            draw.line((x + w, y + radius, x + w, y + h - radius), fill=outline)

    # Draw matches in grid
    for i, match in enumerate(matches):
        row = i // matches_per_row
        col = i % matches_per_row
        
        x = padding + col * (match_width + margin)
        y = padding + row * (match_height + margin) + line_height

        # Draw main box
        draw_rounded_rectangle(x, y, match_width, match_height - margin, 10, (255, 255, 255), (200, 200, 200))

        # Match header
        header_y = y + 20
        header_text = f"{match['qualifier']} - Field: {match['field']}"
        draw.text((x + 20, header_y), header_text, fill=(60, 60, 60), font=header_font)

        # Start time
        time_y = header_y + 45
        time_text = f"Start Time: {match['start_time']}"
        draw.text((x + 20, time_y), time_text, fill=(60, 60, 60), font=font)

        # Alliance boxes
        alliance_box_width = match_width - 40
        alliance_box_height = 80
        alliance_y = time_y + 45

        # Blue Alliance box
        draw_rounded_rectangle(
            x + 20, alliance_y,
            alliance_box_width, alliance_box_height,
            8, (240, 245, 255), (200, 200, 255)
        )
        blue_text = f"Blue Alliance ({match['blue_alliance']['score']} pts)"
        draw.text((x + 30, alliance_y + 10), blue_text, fill=(0, 120, 255), font=font)
        
        # Draw blue alliance teams side by side
        blue_y = alliance_y + 40
        for idx, team_text in enumerate(match['blue_alliance']['teams']):
            team_x = x + 30 + (idx * team_spacing)
            is_our_team = any(part.startswith(match['base_team_number']) for part in team_text.split())
            text_color = (0, 80, 255) if is_our_team else (0, 120, 255)
            if is_our_team:
                text_width = font.getlength(team_text)
                draw.rectangle((team_x, blue_y, team_x + text_width, blue_y + font.size), fill=(220, 230, 255))
            draw.text((team_x, blue_y), team_text, fill=text_color, font=font)

        # Red Alliance box
        draw_rounded_rectangle(
            x + 20, alliance_y + alliance_box_height + 15,
            alliance_box_width, alliance_box_height,
            8, (255, 245, 245), (255, 200, 200)
        )
        red_text = f"Red Alliance ({match['red_alliance']['score']} pts)"
        draw.text((x + 30, alliance_y + alliance_box_height + 25), red_text, fill=(255, 50, 50), font=font)
        
        # Draw red alliance teams side by side
        red_y = alliance_y + alliance_box_height + 55
        for idx, team_text in enumerate(match['red_alliance']['teams']):
            team_x = x + 30 + (idx * team_spacing)
            is_our_team = any(part.startswith(match['base_team_number']) for part in team_text.split())
            text_color = (255, 0, 0) if is_our_team else (255, 50, 50)
            if is_our_team:
                text_width = font.getlength(team_text)
                draw.rectangle((team_x, red_y, team_x + text_width, red_y + font.size), fill=(255, 230, 230))
            draw.text((team_x, red_y), team_text, fill=text_color, font=font)

    # Save with high quality
    image.save(output, format='PNG', dpi=(600, 600), quality=100)

def get_team_matches(url, team_prefix):
    """
    Fetch all matches for a given event
    
    Parameters:
        url (str): The event SKU (e.g., 'RE-V5RC-24-5767')
        team_prefix (str): Currently unused, kept for compatibility
    """
    event_sku = url  # Now we just use the SKU directly
    base_url = "https://www.robotevents.com/api/v2"
    
    headers = {
        "Authorization": ROBOTEVENTS_API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        events_url = f"{base_url}/events?sku%5B%5D={event_sku}&myEvents=false"
        event_response = requests.get(events_url, headers=headers)
        event_response.raise_for_status()
        event_data = event_response.json()
        
        if not event_data.get('data'):
            print(f"No event found for SKU: {event_sku}")
            return None
            
        event_id = event_data['data'][0]['id']
        
        # Get matches using the event ID and division ID, requesting more results
        matches_endpoint = f"{base_url}/events/{event_id}/divisions/1/matches?per_page=250"
        response = requests.get(matches_endpoint, headers=headers)
        response.raise_for_status()
        
        matches_data = response.json()
        
        # Define round order for sorting
        round_order = {
            'Practice': 0,
            'Qualification': 1,
            'Round of 16': 2,
            'R16': 2,
            'QuarterFinal': 3,
            'Quarterfinal': 3,
            'QF': 3,
            'SemiFinal': 4,
            'Semifinal': 4,
            'SF': 4,
            'Final': 5,
            'Finals': 5,
            'F': 5
        }
        
        # Format the matches data
        qualification_matches = []
        elimination_matches = []
        
        def clean_team_name(name):
            # Remove all ANSI color codes before drawing to image
            # Pattern to match the specific format we're seeing
            pattern = r'\x1B\[(?:9[14]m|0m)'  # Matches [94m, [91m, and [0m specifically
            return re.sub(pattern, '', name)

        for match in matches_data['data']:
            # Check if any team in either alliance contains the team_prefix
            teams_in_match = (
                [team['team']['name'] for team in match['alliances'][0]['teams']] +
                [team['team']['name'] for team in match['alliances'][1]['teams']]
            )
            
            if not any(str(team_prefix) in team for team in teams_in_match):
                continue  # Skip this match if team_prefix not found
                
            # Ensure round is a string
            round_type = str(match.get('round', ''))
            
            match_info = {
                'qualifier': clean_team_name(match['name']),
                'round': round_type,
                'field': match['field'],
                'start_time': datetime.fromisoformat(match['scheduled']).strftime('%I:%M %p') if match.get('scheduled') else 'TBD',
                'blue_alliance': {
                    'teams': [clean_team_name(team['team']['name']) for team in match['alliances'][0]['teams']],
                    'score': match['alliances'][0]['score']
                },
                'red_alliance': {
                    'teams': [clean_team_name(team['team']['name']) for team in match['alliances'][1]['teams']],
                    'score': match['alliances'][1]['score']
                }
            }
            
            # Separate matches into qualification and elimination groups
            if round_type in ['Practice', 'Qualification'] or 'Qualifier' in match['name']:
                qualification_matches.append(match_info)
            else:
                elimination_matches.append(match_info)

        # Sort qualification matches by number
        qualification_matches.sort(key=lambda x: int(''.join(filter(str.isdigit, x['qualifier'])) or 0))
        
        # Sort elimination matches by round and then by match number
        def elim_sort_key(match):
            # Extract the match type from the qualifier name (R16, QF, SF, Final)
            match_name = match['qualifier'].upper()
            
            # Determine the round priority
            if 'R16' in match_name:
                round_priority = 2
            elif 'QF' in match_name or 'QUARTER' in match_name:
                round_priority = 3
            elif 'SF' in match_name or 'SEMI' in match_name:
                round_priority = 4
            elif 'FINAL' in match_name:
                round_priority = 5
            else:
                round_priority = 99  # Unknown type
            
            # Extract match numbers (e.g., "1-1" from "QF #1-1")
            numbers = ''.join(c for c in match_name if c.isdigit() or c == '-')
            if '-' in numbers:
                main_num, sub_num = map(int, numbers.split('-'))
            else:
                main_num = int(numbers) if numbers else 0
                sub_num = 0
            
            return (round_priority, main_num, sub_num)
            
        elimination_matches.sort(key=elim_sort_key)
        
        # Combine the sorted lists
        formatted_matches = qualification_matches + elimination_matches
        
        # Create a dictionary to store team records
        team_records = {}
        
        # Process all matches to build records
        for match in matches_data['data']:
            # Skip matches that haven't been scored
            if match['alliances'][0]['score'] == 0 and match['alliances'][1]['score'] == 0:
                continue
                
            blue_score = match['alliances'][0]['score']
            red_score = match['alliances'][1]['score']
            
            # Get teams from both alliances
            blue_teams = [team['team']['name'] for team in match['alliances'][0]['teams']]
            red_teams = [team['team']['name'] for team in match['alliances'][1]['teams']]
            
            # Initialize records for teams if not exists
            for team in blue_teams + red_teams:
                if team not in team_records:
                    team_records[team] = {'wins': 0, 'losses': 0, 'ties': 0}
            
            # Update records based on scores
            if blue_score > red_score:
                for team in blue_teams:
                    team_records[team]['wins'] += 1
                for team in red_teams:
                    team_records[team]['losses'] += 1
            elif red_score > blue_score:
                for team in red_teams:
                    team_records[team]['wins'] += 1
                for team in blue_teams:
                    team_records[team]['losses'] += 1
            else:
                for team in blue_teams + red_teams:
                    team_records[team]['ties'] += 1

        # Format matches with records
        for match_info in formatted_matches:
            # Add records to blue alliance teams
            blue_teams_with_records = []
            for team in match_info['blue_alliance']['teams']:
                record = team_records.get(team, {'wins': 0, 'losses': 0, 'ties': 0})
                blue_teams_with_records.append(
                    f"{team} ({record['wins']}-{record['losses']}-{record['ties']})"
                )
            match_info['blue_alliance']['teams'] = blue_teams_with_records
            
            # Add records to red alliance teams
            red_teams_with_records = []
            for team in match_info['red_alliance']['teams']:
                record = team_records.get(team, {'wins': 0, 'losses': 0, 'ties': 0})
                red_teams_with_records.append(
                    f"{team} ({record['wins']}-{record['losses']}-{record['ties']})"
                )
            match_info['red_alliance']['teams'] = red_teams_with_records
        
        # Add base_team_number to each match for highlighting
        for match_info in formatted_matches:
            match_info['base_team_number'] = team_prefix
        
        # Create BytesIO object for the image
        output = BytesIO()
        create_match_image(formatted_matches, output)
        return output
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/get_events', methods=['POST'])
def get_events():
    team_number = request.form.get('team_id')
    if not team_number:
        return "Please provide a team number", 400
        
    base_url = "https://www.robotevents.com/api/v2"
    headers = {
        "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIzIiwianRpIjoiNmQ5ZTFkOTY2ZjNiZjEzZmIwZGU2M2NlYjk4MzA5YTU4ZDUxZGZjZTFhZjQ3OGQxNzQ0ZGFmZGI1ZTA0MjNmMzhmZjVhMzc5MGFiZDM3MTciLCJpYXQiOjE3MzkyMTk0MjcuMzI5MTE5LCJuYmYiOjE3MzkyMTk0MjcuMzI5MTIxMSwiZXhwIjoyNjg1OTA0MjI3LjMyNDgwOTEsInN1YiI6IjE0Mzg3MyIsInNjb3BlcyI6W119.ATZa9FQKL2eLGWWZhcZB7az4APebuNHgylXeqb-1eVoQbAIroL3aqY9u02eaKpWrjlUhFQ3ekv5EhWz90rucnUkqQz9VAILzYDZfuHgbz2bo6m0cEvls1DfH19a-jZQd4eJLawU8gFBHCrRlGkXWc9QKMD-k394Ssy0aKHwuKVq77YazJgXZiIkJVlIcxdXglThkqpPauVksXuk1K-r88cwmMFgQi_onxQuPEUcF8izs9ITTd2OqCZ58vHWmEZAVSr4qYi4wN7Hn1HKOzoYDHzOVXKyg8FkOcg6CFWcDiosi7ot9rklgPJI_kJXoUGboePwvh_uImyuvJvCU5MYIoFJVxuSBzy2iE8uC-h6oUWMCZIw5UJyTCuh8WYP1Tv9Ym7h_gS2eibd_ICaykpSQUp5yil4PhMao0dcCwuel6THrco72p97TTcHEE62zrNca4mGzSAc1pCypRk6cbD5QeM834A1mXwyKrBPL8QcJsl3tu4nzrmD8PYkCm0Ol1zxYdx41d1Nqhf6pq1eHxbfqgFzcaERcQ1O5jqd08mv1WloGp20wim16cbtQjRKoB7X3NeQgxqbZ4e87NezAfWa96mjIJ9J1bR4nztvGpHdfCaNqEViDS_Eyy3Kgcp7nw1nc7Djzgr5n48-Hradsm4g2Au39ajxDH8OcJg7MsMc6ZSs",
        "accept": "application/json"
    }
    
    try:
        # First, get the team ID using the full team number (e.g., "169A")
        teams_url = f"{base_url}/teams?number%5B%5D={team_number}&myTeams=false"
        team_response = requests.get(teams_url, headers=headers)
        team_response.raise_for_status()
        team_data = team_response.json()
        
        if not team_data.get('data'):
            return f"No team found with number {team_number}", 404
            
        team_id = team_data['data'][0]['id']
        
        # Get events for this specific team
        events_url = f"{base_url}/teams/{team_id}/events?start=2024-06-01"
        response = requests.get(events_url, headers=headers)
        response.raise_for_status()
        events_data = response.json()
        
        # Format the events
        events = []
        for event in events_data['data']:
            events.append({
                'name': event['name'],
                'sku': event['sku'],
                'start_date': event['start'],
                'location': f"{event['location']['city']}, {event['location']['region']}"
            })
        
        # Sort events by date (most recent first)
        events.sort(key=lambda x: x['start_date'], reverse=True)
        
        # Pass both the full team number and base number to the template
        base_team_number = ''.join(filter(str.isdigit, team_number))
        return render_template('events.html', events=events, team_id=base_team_number)
        
    except requests.exceptions.RequestException as e:
        print(f"API Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
        return f"Error fetching events: {str(e)}", 400

@app.route('/view_matches/<event_sku>/<team_prefix>')
def view_matches(event_sku, team_prefix):
    return render_template('view_matches.html', event_sku=event_sku, team_prefix=team_prefix)

@app.route('/get_match_image/<event_sku>/<team_prefix>')
def get_match_image(event_sku, team_prefix):
    try:
        print(f"Generating image for event {event_sku} and team {team_prefix}")  # Debug print
        img_io = get_team_matches(event_sku, team_prefix)
        if not img_io:
            print("No matches found")  # Debug print
            return "No matches found", 404
        
        print("Image generated successfully")  # Debug print
        img_io.seek(0)
        response = send_file(
            img_io,
            mimetype='image/png'
        )
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
    except Exception as e:
        print(f"Error generating image: {str(e)}")  # Debug print
        return f"Error generating image: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)