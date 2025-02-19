# Roboscraper

A Python tool for scraping and analyzing VEX Robotics competition data using the RobotEvents API.

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Roboscraper.git
   cd Roboscraper
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate     # On Windows
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root:
   ```
   ROBOTEVENTS_API_KEY=Bearer your_token_here
   ```
   Replace `your_token_here` with your RobotEvents API token. You can get one from [RobotEvents.com](https://www.robotevents.com/).

## Environment Variables

The following environment variables are required:
- `ROBOTEVENTS_API_KEY`: Your RobotEvents API bearer token

## Usage

Basically, this app will let coaches find full prefix schedules for certain events for their teams. For example, team 1859 Coach Mr. John (example) wants to find his team's schedule. In the first lookup he would want to search for a team at the event that he is at, like say 1859A, then find the event he is at on the table. Then the schedule he presses will be a PDF of every match with a team with the number 1859 and highlight them.

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to your branch
5. Create a Pull Request
