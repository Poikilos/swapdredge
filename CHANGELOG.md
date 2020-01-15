# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).


## [git] - 2020-01-14
### Added
- Aside from standard output, write separate dumps split by
  undisplayable characters (control characters).
- Keep a list of control characters and their descriptions.

### Changed
- Separate stdout (data) and stderr (messages) better (see example in
  README.md with redirect (`>`))
