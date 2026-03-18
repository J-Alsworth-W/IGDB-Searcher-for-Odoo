# Features
The IGDB Searcher is a module for the Odoo platform that uses IGDB, the Internet Game Database, and its API to make queries of IGDB and store the results within Odoo and its database.

The IGDB.com website is a great tool for looking up games and information about games, but the site's Advanced Search feature lacks some important features that this module intends to implement. For example, it is not possible on the site to search for games that released on each of Xbox One AND Playstation 4 AND Nintendo Switch – toggling all three options on and searching will instead return all games released on at least one of those systems, instead of on all three. The same is true for other search criteria such as genres and themes. With the IGDB Searcher for Odoo, this functionality has been added which allows searching of IGDB.com with much greater precision.


<img width="3838" height="1908" alt="image" src="https://github.com/user-attachments/assets/5b8e60d4-60a2-4190-8188-b3c76854452b" />

Additionally, the site does not allow you to add consoles/themes/genres to exclude from the search results. For example, it is not possible either on the site to search for games that released on the Xbox 360 and NOT on the Playstation 3 or the Wii. This is another feature present with the IGDB Searcher to allow greater granularity with user searches.


<img width="3839" height="1904" alt="image" src="https://github.com/user-attachments/assets/2da9ca1d-3bcc-4bd2-b6d7-6f8e16e53338" />

Queries and their returned results are stored on the system, allowing the user to see previous results in the system. Games returned via queries are also stored on the system, and are relationally-linked to the query/queries they returned as valid results for.


<img width="3837" height="826" alt="image" src="https://github.com/user-attachments/assets/bf82b4e2-e3e6-447d-8254-b628ed4dd9f4" />

<img width="3839" height="1908" alt="image" src="https://github.com/user-attachments/assets/4d645c42-5858-487f-8554-237cb5f80477" />

<img width="3838" height="1022" alt="image" src="https://github.com/user-attachments/assets/e383c5c8-70aa-4023-9164-1be78ece7f42" />


# Notes before getting started
This project is still in development with my personal use in mind and as such has been developed for the Odoo platform with which I am familiar and can self-host. 

With regards to usage of this module by other people: while you are able and welcome to download this module (by downloading the igdb_search folder and placing where appropriate in your Odoo system) and use it yourself for personal and non-commercial usage, you will be required to sign up with Twitch for a free account, enable their 2FA, and register an application in the Twitch Developer Portal, from where you can generate a Client Secret and Client ID which are required to enter into the IGDB Searcher Odoo module's configuration to be able to search IGDB.com's database. With regards to the steps involving Twitch, all of this is explained in the IGDB.com API documentation available at https://api-docs.igdb.com/#account-creation.

# Gratitudes
My thanks go to IGDB and Twitch for making the IGDB.com API free for non-commercial usage, and for making and maintaining the site more generally. The generous API terms allow personal projects like this one to exist, and the IGDB.com site as a whole has helped me win many rounds of video game music trivia with my friends!
