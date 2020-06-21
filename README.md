# SeCov

> Determine the security coverage from code project.

---

## Description
SeCov extracts all the routes and their matching security unit-tests from a given set of code files
and stores it in a local SQLite database.

SeCov was built in a goal to determine the security unit-tests coverage in a project,
but can easily be used for other stuff like WhiteBox penetration tests aid tool.

### Highlights
- Only [Java Spring RequestMapping annotations][springdocumentation] are currently supported for the routes parsing
- SeCov defines it's own annotation (take a look at the `annotation-classes` directory for Java Spring example.
The annotation is written like the following:
`@CoveredRoute(path="/my-covered-route", method="PUT")`

---

## Installation

```bash
# Clone the repository.
git clone https://github.com/rotemreiss/secov.git

# Install Python dependencies.
cd secov
pip3 install -r requirements.txt
```

### Setup
- Copy `config.py.template` to `config.py`\
  ```cp config.py.template config.py```
- You may now change the SQLite DB file location

---

## Recommended Python Version
SeCov was developed and tested only with __Python3__.

---

## Usage

- List all options\
  ```python main.py --help```
- Scan a project\
  ```python main.py -p my_super_secured_project -d /Users/johndoe/projects/my-secured-project/```

---
## Roadmap
- Support other languages and frameworks (PHP will probably be the next). Contributions are most welcome)
- Generalize the annotation parsing code
- Support inputs within routes (more annotations parsing)
- Package as a python package

---
## Contributing
Feel free to fork the repository and submit pull-requests.

---

## Support

[Create new GitHub issue][newissue]

Want to say thanks? :) Message me on <a href="https://www.linkedin.com/in/reissr" target="_blank">Linkedin</a>


---

## License

[![License](http://img.shields.io/:license-mit-blue.svg?style=flat-square)](http://badges.mit-license.org)

- **[MIT license](http://opensource.org/licenses/mit-license.php)**

<!-- Markdown helper -->
[springdocumentation]: https://docs.spring.io/spring/docs/current/javadoc-api/org/springframework/web/bind/annotation/RequestMapping.html
[newissue]: https://github.com/rotemreiss/secov/issues/new