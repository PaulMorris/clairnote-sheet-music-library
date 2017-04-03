/* JS for Clairnote Music Notation: Sheet Music Archive */
"use strict";

// fixes IE8 - lack of support for getElementsByClassName
// but we break IE8 elsewhere... so maybe remove this?
if (!document.getElementsByClassName) {
    document.getElementsByClassName = function (className) {
        return this.querySelectorAll("." + className);
    };
    Element.prototype.getElementsByClassName = document.getElementsByClassName;
}

(function() {
  var styleBoxes = {},
      instrumentBoxes = {},
      composerBoxes = {},
      lunrIndex,
      timeout,
      input = document.getElementById("search-box"),
      searchResults = document.getElementById('search-results');

  var oneBoxAnchorClickHandler = function () {
      var id = this.parentNode.firstChild.id,
          box = document.getElementById(id);
      box.checked = !box.checked;
  };

  // see http://www.somacon.com/p117.php
  var multiBoxToggleHandler = function (fieldName, formName, checkValue) {
      var boxes = document.forms[formName].elements[fieldName];

      // set the check value for the group of checkboxes
      boxes.forEach(function (box) {
          box.checked = checkValue;
      });
  };

  var boxesToObject = function (boxes) {
    var obj = {};
    boxes.forEach(function (box) {
        if (box.checked) {
            obj[box.id] = true;
        }
    })
    return obj;
  };

  var displayActiveFilters = function (keys, id) {
      var span = document.getElementById(id),
          text;
      if (keys.length) {
          text = ':';
          keys.forEach(function (key) {
              text += (' ' + key + ',');
          });
          // slice off the last comma
          span.textContent = text.slice(0, -1);
      } else {
          span.textContent = '';
      }
  };

  var refreshBoxesState = function () {
      styleBoxes = boxesToObject(document.forms['style-form'].elements['s-box']);
      instrumentBoxes = boxesToObject(document.forms['instrument-form'].elements['i-box']);
      composerBoxes = boxesToObject(document.forms['composer-form'].elements['c-box']);
      displayActiveFilters(Object.keys(styleBoxes), 'styles-active-filters');
      displayActiveFilters(Object.keys(instrumentBoxes), 'instruments-active-filters');

      var composers = Object.keys(composerBoxes).map(function (c) { return composerLookup[c][0] });
      displayActiveFilters(composers, 'composers-active-filters');
  };

  var showFiltersButton = function (id) {
      document.getElementById(id).style.display = 'block';
      document.getElementById('dark-overlay').style.display = 'block';
      // set 'html' element so the page won't scroll in the background
      document.documentElement.style.overflowY = 'hidden';
  };

  var darkOverlayClick = function () {
      var about = document.getElementById('about'),
          aboutWasShowing = about.style.display === 'block';
      about.style.display = 'none';
      document.getElementById('style-filters').style.display = 'none';
      document.getElementById('instrument-filters').style.display = 'none';
      document.getElementById('composer-filters').style.display = 'none';
      document.getElementById('dark-overlay').style.display = 'none';
      // set 'html' element so the page will scroll in the background again
      document.documentElement.style.overflowY = 'scroll';
      if (!aboutWasShowing) {
          refreshBoxesState();
          searchAndFilter();
      }
  };

  var licenseLookup = {
      'pd0': ["PD", "Public Domain", "http://creativecommons.org/publicdomain/zero/1.0/"],
      'by3': ["CC BY 3.0", "Creative Commons Attribution 3.0", "http://creativecommons.org/licenses/by/3.0/"],
      'by4': ["CC BY 4.0", "Creative Commons Attribution 4.0", "http://creativecommons.org/licenses/by/4.0/"],
      'by-sa3': ["CC BY-SA 3.0", "Creative Commons Attribution-ShareAlike 3.0", "http://creativecommons.org/licenses/by-sa/3.0/"],
      'by-sa4': ["CC BY-SA 4.0", "Creative Commons Attribution-ShareAlike 4.0", "http://creativecommons.org/licenses/by-sa/4.0/"]
  };

  var makeAnchor = function (text, href, title, target, className) {
      var a = document.createElement('a');
      a.href = href;
      a.textContent = text;
      if (title) { a.title = title; }
      if (target) { a.target = target; }
      if (className) { a.className = className; }
      return a;
  };

  var makeDivider = function () {
      return document.createTextNode(' | ');
  };

  var makeResultLi = function (id, item) {
      var li = document.createElement('li'),
          strong = document.createElement('strong'),
          line2 = document.createElement('span'),
          divider = ' | ',
          pathToDir = "http://clairnote.org/sheet-music-files/" + item[4] + "/",
          composer = composerLookup[item[1]][0];

      // FIRST LINE
      // item[2] is title
      strong.textContent = item[2]
          // opus in parentheses, if it exists
          + (item[7].trimLeft() ? ' (' + item[7]  + ')' : '')
          + ' — '
          // Traditional ends up with an extra space in front because it has no first initial...
          + (composer === " Traditional" ? composer.trimLeft() : 'by ' + composer)
          + ' — for ' + item[3].join(', ');

      // previously this was used for instruments, is it needed for some reason?
      // item[3].toString().split(',').join(', ')

      // SECOND LINE
      line2.className = 'line-two';
      // item[0] is style
      line2.textContent = item[0] + divider
          // date
          + (item[9] ? item[9] + divider : '')
          // poet / words / lyricist
          + (item[8] ? 'Words: ' + item[8] + divider : '')
          + (item[10] ? 'Arrangement: ' + item[10] + divider : '');

      // FILES AND LINKS
      if (item[5]) {
          // single ly file, item[5] is the file name without the extension
          var path = pathToDir + item[5];
          line2.appendChild(makeAnchor("LETTER PDF", path + '-let.pdf', 'Letter Size PDF File', '_blank'));
          line2.appendChild(makeDivider());
          line2.appendChild(makeAnchor("A4 PDF", path + '-a4.pdf', 'A4 Size PDF File', '_blank'));
          line2.appendChild(makeDivider());
          line2.appendChild(makeAnchor("MIDI", path + '.mid', 'MIDI File', '_blank'));
          line2.appendChild(makeDivider());
          line2.appendChild(makeAnchor("LY", path + '.ly', 'LilyPond File', '_blank'));
      } else {
          // multiple ly files, just link to the directory, path for multi-file records only goes to directory not file
          line2.appendChild(makeAnchor("PDF, MIDI, and LilyPond Files", pathToDir,
              'This work involves multiple PDF, MIDI, and/or LilyPond Files', '_blank'));
      }
      line2.appendChild(makeDivider());
      line2.appendChild(makeAnchor("MP", "http://www.mutopiaproject.org/cgibin/piece-info.cgi?id=" + id,
          'Mutopia Project Page', '_blank'));

      line2.appendChild(makeDivider());
      var licenseData = licenseLookup[item[6]];
      line2.appendChild(makeAnchor(licenseData[0], licenseData[2], licenseData[1], '_blank'));

      li.className = 'search-result';
      li.appendChild(strong);
      li.appendChild(document.createElement('br'));
      li.appendChild(line2);
      return li;
  };

  var displaySearchResults = function (results, store) {
      searchResults.innerHTML = '';
      // If there are any results, iterate over them.
      if (results.length) {
          results.forEach(function (id) {
              searchResults.appendChild(makeResultLi(id, store[id]));
          });
      } else {
          var li = document.createElement('li');
          li.class = 'search-result';
          li.textContent = 'No results found';
          searchResults.appendChild(li);
      }
      // update 'showing n of x'
      document.getElementById('showing')
          .textContent = '| ' + results.length + ' results out of ' + recsSortedIds.length;
  }

  var applyFilters = function (ids, store, filters, index) {
      return ids.filter(function (id) {
          var item = store[id];
          return filters[item[index]];
      });
  };

  // instruments is different because it is an array, more than one possible
  var applyInstrumentFilters = function (ids, store, filters, index) {
      return ids.filter(function (id) {
          var i,
              item = store[id],
              instruments = item[index];
          for (i = 0; i < instruments.length; i += 1) {
              if (filters[instruments[i]]) {
                  return true;
              }
          }
          return false;
      });
  };

  var searchAndFilter = function () {
      var query = input.value.trimLeft(),
          ids, ids2, ids3, ids4,
          lunrResults;
      if (query) {
          lunrResults = lunrIndex.search(query);
          ids = lunrResults.map(function (item) { return item.ref; });
      } else {
          // .slice() not needed since ids is not mutated
          ids = recsSortedIds;
      }
      // apply filters to results
      ids2 = Object.keys(styleBoxes).length ? applyFilters(ids, recsjson, styleBoxes, 0) : ids;
      ids3 = Object.keys(composerBoxes).length ? applyFilters(ids2, recsjson, composerBoxes, 1) : ids2;
      ids4 = Object.keys(instrumentBoxes).length ? applyInstrumentFilters(ids3, recsjson, instrumentBoxes, 3) : ids3;
      displaySearchResults(ids4, recsjson);
  };

  var doNotPropagate = function (event) {
      if (event.stopPropagation) {
          event.stopPropagation();
      } else {
          // IE 6-9
          event.cancelBubble = true;
      }
      return false;
  };

  // initialize everything
  window.onload = function () {
      var i,
          boxAnchors = document.getElementsByClassName('f-link');

      // Initalize lunr with the fields it will be searching on.
      lunrIndex = lunr(function () {
          this.ref('id');
          this.field('title', { boost: 10 });
          this.field('style');
          this.field('composer', { boost: 3 });
          this.field('instruments');
          this.field('opus');
          this.field('poet');
          this.field('date');
          this.field('arranger');
      });

      // Add the data to lunr index
      recsSortedIds.forEach(function (id) {
          var item = recsjson[id];
          lunrIndex.add({
              'id': id,
              'style': item[0],
              'composer': composerLookup[item[1]][0],
              'title': item[2],
              'instruments': item[3].join(' '),
              'opus': item[7],
              'poet': item[8],
              'date': item[9],
              'arranger': item[10]
          });
      });

      // add checkbox listeners for anchor tags
      for (i = 0; i < boxAnchors.length; i += 1) {
          boxAnchors[i].addEventListener("click", oneBoxAnchorClickHandler, false);
      }

      // add event listeners
      document.getElementById("search-button").addEventListener("click", searchAndFilter, false);
      document.getElementById("search-box").addEventListener("keyup", function(event) {
          event.preventDefault();
          if (event.which == 13) {
              searchAndFilter();
              return false;
          }
      });

      document.getElementById("styles-filter-button").addEventListener("click", function() {showFiltersButton('style-filters');}, false);
      document.getElementById("instruments-filter-button").addEventListener("click", function () {showFiltersButton('instrument-filters');}, false);
      document.getElementById("composers-filter-button").addEventListener("click", function() {showFiltersButton('composer-filters');}, false);
      document.getElementById("about-button").addEventListener("click", function () {showFiltersButton('about');}, false);

      document.getElementById("dark-overlay").addEventListener("click", darkOverlayClick, false);

      document.getElementById('style-filters').addEventListener('click', doNotPropagate, false);
      document.getElementById('instrument-filters').addEventListener('click', doNotPropagate, false);
      document.getElementById('composer-filters').addEventListener('click', doNotPropagate, false);
      document.getElementById('about').addEventListener('click', doNotPropagate, false);

      document.getElementById("s-all").addEventListener("click", function () {multiBoxToggleHandler("s-box", 'style-form', true); }, false);
      document.getElementById("s-none").addEventListener("click", function () {multiBoxToggleHandler("s-box", 'style-form', false); }, false);
      document.getElementById("i-all").addEventListener("click", function () {multiBoxToggleHandler("i-box", 'instrument-form', true); }, false);
      document.getElementById("i-none").addEventListener("click", function () {multiBoxToggleHandler("i-box", 'instrument-form', false); }, false);
      document.getElementById("c-all").addEventListener("click", function () {multiBoxToggleHandler("c-box", 'composer-form', true); }, false);
      document.getElementById("c-none").addEventListener("click", function () {multiBoxToggleHandler("c-box", 'composer-form', false); }, false);

      refreshBoxesState();
      // clear loading message
      document.getElementById('search-results').innerHTML = 'Loaded and ready.  Do a search and/or apply a filter to find some sheet music.';
  }
})();
