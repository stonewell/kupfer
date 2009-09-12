#!/usr/bin/env python
# Copyright (C) 2009  Ulrik Sverdrup <ulrik.sverdrup@gmail.com>
#               2008  Christian Hergert <chris@dronelabs.com>
#               2007  Chris Halse Rogers, DR Colkitt
#                     David Siegel, James Walker
#                     Jason Smith, Miguel de Icaza
#                     Rick Harding, Thomsen Anders
#                     Volker Braun, Jonathon Anderson 
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division

"""
This module provides relevance matching and formatting of related strings
based on the relevance.  It is borrowed from Gnome-Do with modifications
to fit nicely into python.

>>> import relevance
>>> print relevance.score('hi there dude', 'hi dude')
0.745628698225
>>> relevance.formatCommonSubstrings('hi there dude', 'hi dude')
'<b>hi </b>there <b>dude</b>'
"""

def formatCommonSubstrings(main, other, format = '<b>%s</b>'):
    """
    Creates a new string using @format to highlight matching substrings
    of @other in @main.
    
    Returns: a formatted str
    
    >>> formatCommonSubstrings('hi there dude', 'hi dude')
    '<b>hi </b>there <b>dude</b>'
    """
    length = 0
    result = ''
    match_pos = last_main_cut = 0
    lower_main = main.lower()
    other = other.lower()
    
    for pos in range(len(other)):
        matchedTermination = False
        for length in range(1, 1 + len(other) - pos + 1):
            tmp_match_pos  = lower_main.find(other[pos:pos + length])
            if tmp_match_pos < 0:
                length -= 1
                matchedTermination = False
                break
            else:
                matchedTermination = True
                match_pos = tmp_match_pos
        if matchedTermination:
            length -= 1
        if 0 < length:
            # There is a match starting at match_pos with positive length
            skipped = main[last_main_cut:match_pos - last_main_cut]
            matched = main[match_pos:match_pos + length]
            if len(skipped) + len(matched) < len(main):
                remainder = formatCommonSubstrings(
                    main[match_pos + length:],
                    other[pos + length:],
                    format)
            else:
                remainder = ''
            result = '%s%s%s' % (skipped, format % matched, remainder)
            break
    
    if result == '':
        # No matches
        result = main
    
    return result

def score(s, query):
    """
    A relevancy score for the string ranging from 0 to 1
    
    @s: a str to be scored
    @query: a str query to score against
    
    Returns: a float between 0 and 1
    
    >>> print score('terminal', 'trml')
    0.735098684211
    >>> print score('terminal', 'term')
    0.992302631579
    >>> print score('terminal', 'try')
    0.0
    >>> print score('terminal', '')
    1.0
    >>> print score('terminal', 'yl')
    0.0
    >>> print score('terminal', 'tlm')
    0.0
    """
    if not query:
        return 1.0
    
    score = 0.0
    ls = s.lower()
    
    # Find the shortest possible substring that matches the query
    # and get the ration of their lengths for a base score
    first, last = _findBestMatch(ls, query)
    if first == -1:
        return .0

    score = len(query) / (last - first)

    # Now we weight by string length so shorter strings are better
    score *= .7 + len(query) / len(s) * .3
    
    # Bonus points if the characters start words
    good = 0
    bad = 1
    firstCount = 0
    for i, c in enumerate(ls[first:last-1]):
        if c in " -":
            if ls[i + 1] in query:
                firstCount += 1
            else:
                bad += 1
    
    # A first character match counts extra
    if query[0] == ls[0]:
        firstCount += 2
        
    # The longer the acronym, the better it scores
    good += firstCount * firstCount * 4
    
    # Better yet if the match itself started there
    if first == 0:
        good += 2
        
    # Super bonus if the whole match is at the beginning
    if last == len(query) - 1:
        good += last + 4
        
    # Super duper bonus if it is a perfect match
    if query == ls:
        good += last * 2 + 4
        
    if good + bad > 0:
        score = (score + 3 * good / (good + bad)) / 4
        
    # This fix makes sure tha tperfect matches always rank higher
    # than split matches.  Perfect matches get the .9 - 1.0 range
    # everything else lower
    
    if last - first == len(query):
        score = .9 + .1 * score
    else:
        score = .9 * score
    
    return score
    
def _findBestMatch(s, query):
    """
    Finds the shortest substring of @s that contains all characters of query
    in order.
    
    @s: a str to search
    @query: a str query to search for
    
    Returns: a two-item tuple containing the start and end indicies of
             the match.  No match returns (-1,-1).

    >>> _findBestMatch('terminal', 'yl')
    (-1, -1)
    >>> _findBestMatch('terminal', 'term')
    (0, 4)
    >>> _findBestMatch('terminal', 'trml')
    (0, 8)
    >>> _findBestMatch('teerminal', 'erml')
    (2, 9)
    >>> _findBestMatch('terminal', 'e')
    (1, 2)
    """
    bestMatch = -1, -1
    
    # Find the last instance of the last character of the query
    # since we never need to search beyond that
    lastChar = s.rfind(query[-1])
    
    # No instance of the character?
    if lastChar == -1:
        return bestMatch

    # Loop through each instance of the first character in query
    index = s.find(query[0])

    queryLength = len(query)
    lastIndex = lastChar - len(query) + 1
    while 0 <= index <= lastIndex:
        # See if we can fit the whole query in the tail
        # We know the first char matches, so we dont check it.
        cur = index + 1
        qcur = 1
        while qcur < queryLength:
            # find where in the string the next query character is
            # if not found, we are done
            cur = s.find(query[qcur], cur, lastChar + 1)
            if cur == -1:
                return bestMatch
            cur += 1
            qcur += 1

        # take match if it is shorter
        # if perfect match, we are done
        if bestMatch[0] == -1 or (cur - index) < (bestMatch[1] - bestMatch[0]):
            bestMatch = (index, cur)
            if cur - index == queryLength:
                break

        index = s.find(query[0], index + 1)

    return bestMatch

if __name__ == '__main__':
    import doctest
    doctest.testmod()
