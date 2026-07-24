# Features
The IGDB Searcher is a module for the Odoo platform that uses IGDB, the Internet Game Database, and its API to make queries of IGDB and store the results within Odoo and its database.

The IGDB.com website is a great tool for looking up games and information about games, but the site's Advanced Search feature lacks some important features that this module intends to implement. For example, it is not possible on the site to search for games that released on each of Xbox One AND Playstation 4 AND Nintendo Switch – toggling all three options on and searching will instead return all games released on at least one of those systems, instead of on all three. The same is true for other search criteria such as genres and themes. With the IGDB Searcher for Odoo, this functionality has been added which allows searching of IGDB.com with much greater precision.


<img width="3838" height="1908" alt="Screenshot 2026-07-24 160317" src="https://github.com/user-attachments/assets/cb1ff34c-6520-4a30-bd6f-bd155a06f338" />

Additionally, the site does not allow you to add consoles/themes/genres to exclude from the search results. For example, it is not possible either on the site to search for games that released on the Xbox 360 and NOT on the Playstation 3 or the Wii. This is another feature present with the IGDB Searcher to allow greater granularity with user searches.


<img width="3839" height="1906" alt="Screenshot 2026-07-24 160518" src="https://github.com/user-attachments/assets/ac894cd0-91de-4608-94fb-25dfbd11ea39" />

Queries and their returned results are stored on the system, allowing the user to see previous results in the system. Games returned via queries are also stored on the system, and are relationally-linked to the query/queries they returned as valid results for.

<img width="3837" height="1904" alt="Screenshot 2026-07-24 160808" src="https://github.com/user-attachments/assets/5b32b558-3702-49a1-986a-6ab07c323250" />

<img width="3837" height="1903" alt="Screenshot 2026-07-24 161039" src="https://github.com/user-attachments/assets/e279fabe-ad87-40c5-a346-bd03bd1b22b5" />

<img width="3838" height="1904" alt="Screenshot 2026-07-24 162648" src="https://github.com/user-attachments/assets/89b6a455-f2a6-4681-bea9-5065b7d77c41" />


# Notes before getting started
This project is still in development with my personal use in mind and as such has been developed for the Odoo platform with which I am familiar and can self-host. 

With regards to usage of this module by other people: while you are able and welcome to download this module (by downloading the igdb_search folder and placing where appropriate in your Odoo system) and use it yourself for personal and non-commercial usage, you will be required to sign up with Twitch for a free account, enable their 2FA, and register an application in the Twitch Developer Portal, from where you can generate a Client Secret and Client ID which are required to enter into the IGDB Searcher Odoo module's configuration to be able to search IGDB.com's database. With regards to the steps involving Twitch, all of this is explained in the IGDB.com API documentation available at https://api-docs.igdb.com/#account-creation.

# Gratitudes
My thanks go to IGDB and Twitch for making the IGDB.com API free for non-commercial usage, and for making and maintaining the site more generally. The generous API terms allow personal projects like this one to exist, and the IGDB.com site as a whole has helped me win many rounds of video game music trivia with my friends!
