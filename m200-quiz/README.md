Retrieve Quiz Questions
=======================

This logic will download all quiz questions.

First execute `browser.js` in e.g. Chrome developer tools, this will compile
all known questions and export the data as json.

Then execute `create-anki-deck.py`, which will load the json and create a deck.

## Example

```
// https://m200-quiz-production.up.railway.app
> await downloadAllQuizQuestions('A');
```

```
$ ./create-anki-deck.py
Creating deck: M200 Part A
```

## Dependencies
- https://github.com/DamianZaremba/anki-drag-and-drop
- https://ankiweb.net/shared/info/1744375818

Note: The questions are copyrighted material and only for personal usage relating to a subscribed course
