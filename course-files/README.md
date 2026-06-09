Retrieve Course Files
=====================

This logic will download all course files for a given course.

First execute `browser.js` in e.g. Chrome developer tools, this will download
all files in each section, with the relevant section & file name encoded.

Then execute `arrange_files.py`, this will parse the encoded file names and
re-structure them into the same hierarchy as they were downloaded.

## Example

```
// https://app.mcaonlinecourses.com
> await downloadAllCourseFiles('624536a58593f0001640aa7c');
Fred~~M200~~VGhlIEludHJvZHVjdGlvbi9NMjAwIEZsYXNoY2FyZHMgaW50cm8ucGRm
```

```
$ ./arrange_files.py ~/Downloads ~/Fred\ Online\ Oral\ Prep/Course\ Files/
Moving /Users/damian/Downloads/Fred~~M200~~VGhlIEludHJvZHVjdGlvbi9NMjAwIEZsYXNoY2FyZHMgaW50cm8ucGRm.pdf to The Introduction/M200 Flashcards intro.pdf
```

Note: The downloads are copyrighted material and only for personal usage relating to a subscribed course
