# PROXY PROXY PROXY!

🚧 **Under Construction** 🚧  
This project is still incomplete and is in active development and alpha stage.

- [x] GitHub Actions: Build and run scraper  
- [x] Scraper Script  
- [x] Initial version of the Web Server  
- [x] Connect the domain  
- [X] Add checker and categorize by location  
- [ ] Complete the web server and add some UI 


## What's the Idea?  
Since I'm a lazy person and almost every task I worked on required proxies, I created this repository to save myself from constantly searching for proxies.

## How Does It Work?  
The process involves collecting proxies from multiple sources, checking them, and saving them to GitHub. All of this is automated using GitHub Actions.  
Finally, the proxies are deployed on **Vercel** via an **Express.js** server.

## What's the Project Structure?  
- **GitHub Actions**  
  Builds the Go files, runs the scraper for proxy collection, and executes the checker for validating proxies.

- **Scraper Script**  
  Gathers proxies using both Python and Go to combine simplicity with speed in the collection process.

- **Checker Script**  
  Verifies and categorizes proxies using the **X-Ray Core**.

- **Web Server**  
  An Express-based web server deployed on Vercel, providing features like limiting proxies or fetching configurations directly from Telegram.
