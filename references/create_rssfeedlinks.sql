# Create rssfeed_links table for articles database
# http://dev.mysql.com/doc/refman/5.7/en/create-table.html

DROP TABLE IF EXISTS rssfeed_links;
#@ _CREATE_TABLE_
CREATE TABLE rssfeed_links
(
	title		VARCHAR(200) NOT NULL,
	link		VARCHAR(200) NOT NULL,
	PRIMARY KEY (link),
	published	DATETIME NOT NULL,
	summary		VARCHAR(2000),
	story_id	VARCHAR(50),
	rss_link	VARCHAR(100) NOT NULL
) ENGINE = InnoDB;
#@ _CREATE_TABLE_
