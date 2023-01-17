
--DROP TABLE users;
CREATE TABLE IF NOT EXISTS users (
	id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
	email TEXT NOT NULL,
	first_name TEXT NOT NULL,
	last_name TEXT NOT NULL,
	password_hash TEXT NOT NULL,
	gpt_session_token TEXT,
	history TEXT
);

-- DROP TABLE materials;
CREATE TABLE IF NOT EXISTS materials (
	id INTEGER PRIMARY KEY,
	`name` TEXT,
	`uid` INTEGER,
	uuid TEXT,
	query TEXT,
	selected TEXT,
	keyPoints TEXT,
	quiz TEXT,
	mcq TEXT,
	summary TEXT,
	openendedArray TEXT DEFAULT '{}',
	mcqArray TEXT DEFAULT '{}',
	keyPointsArray TEXT DEFAULT '{}',
	summaryResult TEXT DEFAULT '',
	`status` TEXT,
	created TEXT,
	privacy TEXT DEFAULT 'private'
);

--DROP TABLE quizAttempts;
CREATE TABLE IF NOT EXISTS quizAttempts (
	id INTEGER PRIMARY KEY,
	uuid INTEGER,
	answers TEXT,
	`uid` INTEGER
);

INSERT INTO
	users (
		email,
		first_name,
		last_name,
		password_hash,
		gpt_session_token
	)
VALUES
	(
		'hello@gptutor.com',
		'test',
		'user',
		'8cf2283ad6ef0a3266059b418a73f8479338233ea2c4bcd3c1f51c39f13ae7dc',
		'abc'
	);
