# Google Scholar Review Filter

This project was made to help researchers in the literature review process using Google Scholar. Unlike other papers repositories, Google Scholar does not have an option to filter results by title, abstract, or keywords. Thus, the queries made return a huge amount of papers, which makes it impossible to analyze all returned papers. Because of this, this project presents a solution for the automatic search of articles and filtering of TITLE-ABS-KEY using the PICOC methodology terms.



## Requirements
To run this project you will need:

* Python 3
* Python pip

Then clone the repository and run:

* ``pip install -r requirements.txt``

## How to use

### Configuration

Copy or rename the ``config.ex.ini`` to ``config.ini`` and set up the config file:

* **chromedriver**: Chromedriver executable Path. This project uses the Selenium WebDriver. It is necessary to download the [chormedriver](https://chromedriver.chromium.org/downloads) compatible with you system.
* **query**: Google Scholar search string with a maximum of 256 characters. Google Scholar truncates the string with more than this size.
* **start_year** and **end_year**: This script searches for papers year by year because Google Scholar only allows 1000 of paper by query.
* **picoc** : The terms are those you want to be found in the papers title, abstract, or keywords. The terms have to be separated by "|".

### To run

After the configuration, run the following code:

* ``python scholar.py``

The selenium will open a new Google Chrome tab and perform the search by itself.

## Monitoring

Sometimes a Captcha shows up on the browser. It needs to be fixed manually. When it occurs, the following message will pop up on the terminal:

* ``Captcha found! You need to fill it on browser to continue. Go to the terminal and type 'y' when the Captcha be solved``

The process will only continue if the Captcha be solved. 
