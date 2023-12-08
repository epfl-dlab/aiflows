### Dependencies

```
# install node modules for react landing page
cd website
npm install
```
```
# install sphinx for API documentation
pip install sphinx
pip install sphinxawesome-theme
pip install sphinx_copybutton
pip install sphinx-book-theme==1.0.1
pip install myst-parser[sphinx]
```

### Building API Documentation

```
# build API documentation
cd public/docs
make clean
sphinx-apidoc -o source/ ../../../aiflows
make html
```

### Building Website

For testing purposes:
```
npm run start
```

For pushing the newest version:
Add this line to package.json, just above `"name":"my-app",`:
```
  "homepage": ".",
```
Then execute:
```
npm run deploy
```

ToDo: do we need to copy .nojekyll to gh-pages branch?
