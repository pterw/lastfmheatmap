# Last.fm Heatmap

This tool gathers information about a last.fm user's listening habits (songs listened to per day, organized by month) and displays it as a heatmap.
The output heatmap is organized into tiles with the rocket_r colour pallette from the seaborn library.
The heatmap is log adjusted so that a day where there is an abnormal ammount of songs played does not affect the visual representation of the others excessively.
White boxes represent days where no music or songs where listened to.
X-axis represents the year and month in YY-MM format.
Y-axis represents days of the month up to 31, days with less than 31 days have their last day in white.

## Link To Project (Currently Offline!)

https://lastfmproject-d6593f6b5f86.herokuapp.com/

**NOTE:** I have to login to heroku for the web app to be accessible to others.

## Preview: 

**![alt text](https://i.imgur.com/OYzFq0I.png)**

**As of 2024-08-02, the project aims to be updated with the following:**

-Better placement of heatmap 

-Changing title of the heatmap to include last.fm username

-Less clutter on ticks

-Better representation of months with less than 31 days by using gray tiles for non-existant days. (e.g. June 31st would be a gray box.)

-Updates to layout of webapp

-Ability to download your heatmap

-Ability to change colour scheme via color palettes available in seaborn

-Improving axis titles to be more descriptive

**Additional planned updates:**

-Faster processing for accounts with >100,000 scrobbles

-Mobile compatibility

-Interactivity when hovering over a tile, displaying #of songs played that day

-Option to highlight days where most listen to song was listend to

-Option to select one of user's top 10 artists and highlight days on which their music was played.

-GUI



  **Future ideas:**

  -Implementing a "mood" heatmap (Music Mood Map), where songs are classed as "happy", "neutral", "sad" (Plan to fetch tags using RYM or MusicBrainz) 
  
  -Implementing a "new music" heatmap (Music Discovery Heatmap) that highlights days where new artists were listened to the most. 
  
  -Implementing a genre map (Music Genre Map) where the most predominant genre listened to in a day is highlighted a certain colour. (Possibly a pie chart for overall genre listening?)
  
  -Adding features that are limited to last.fm pro accounts (e.g. last.month, historical reports, tag timeline & advanced discovery charts)


For any commments & suggestions, feel free to contact me!
