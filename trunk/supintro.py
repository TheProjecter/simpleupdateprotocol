#!/usr/bin/env python
#
# Copyright 2008 FriendFeed
# Author: Paul Buchheit
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


"""
SUP (Simple Update Protocol) is to a simple and compact "ping feed" that
web services can produce in order to alert the consumers of their feeds when
a feed has been updated. This reduces update latency and improves efficiency
by eliminating the need for frequent polling.

Benefits include:
 - Simple to implement. Most sites can add support with only few lines
   of code if their database already stores timestamps.
 - Works over HTTP, so it's very easy to publish and consume.
 - Cacheable. A SUP feed can be generated by a cron job and
   served from a static text file or from memcached.
 - Compact: updates can be about 21 bytes each. (8 bytes with gzip encoding)
 - Does not expose usernames or secret feed urls (such as Google Reader
   Shared Items feeds)

SUP is designed to be especially easy for feed publishers to create.
It's not ideal for small feed consumers because they will only be interested
in a tiny fraction of the updates, however intermediate services such as
Gnip or others can easily consume a SUP feed and convert it into a
subscribe/push model using XMPP or HTTP callbacks.

Sites wishing to produce a SUP feed must do two things:
 - Add a special "link" tag to their SUP enabled Atom or RSS feeds. This
   "link" tag includes the feed's SUP-ID and the URL of the appropriate
   SUP feed.
 - Generate a SUP feed which lists the SUP-IDs of all recently updated
   feeds.

Feed consumers can add SUP support by:
 - Storing the SUP-IDs of the Atom/RSS feeds they consume.
 - Watching for those SUP-IDs in their associated SUP feeds.

By using SUP-IDs instead of feed urls, we avoid having to expose
the feed url, avoid URL canonicalization issues, and produce a
more compact update feed (because SUP-IDs can be a simple random number).

Because it is still possible to miss updates due to server errors or other
malfunctions, SUP does not completely eliminate the need for polling. However,
when using SUP, feed consumers can reduce polling frequency while
simultaniously reducing update latency. For example, if a site such as
FriendFeed switched from polling feeds every 30 minutes to polling every
300 minutes (5 hours), and also monitored the appropriate SUP feed every
3 minutes, the total amount of feed polling would be reduced by about 90%,
and new updates would typically appear 10 times as fast.
"""

import calendar
import simplejson
import datetime
import hashlib

def rfc_3339_time(date):
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")

def generate_sup_id(username):
    """ A SUP-ID is a short, mostly-unique string used to
    identify an Atom/RSS feed. A particular feed should
    always have the same SUP-ID, but it's ok if different
    feeds sometimes have the same SUP-ID.

    To avoid encoding issues, a valid SUP-ID is a short string
    composed of ASCII letters, numbers, or hyphens (regex [a-zA-Z0-9-]).
    Publishers are otherwise free to assign SUP-IDs in any way they
    choose, however it is important that they do not change.

    One option is to generate a random number and store it along with
    the appropriate database entity, such as a user account. Another
    reasonable option is to simple use a hash of an exising identifier,
    such as a username or userid.

    SUP-IDs should be mostly unique, however they don't need to be
    completely unique since collisions will simply cause "false pings",
    which are mostly harmless (assuming collisions are relatively rare).

    This function demonstrates how to generate a SUP-ID based on a hash
    of the username.
    """

    # first encode the username as utf-8
    if isinstance(username, unicode):
        username = username.encode("utf-8")
    else:
        username = str(username)

    # Then compute the hash and return a short, 8 character
    # prefix of the hex value.
    return hashlib.md5(username).hexdigest()[:8]


def make_sup_link(username, for_rss=False):
    """
    Atom/RSS feeds that support SUP must include a link tag to announce
    the SUP-ID and URL of the SUP feed.

    The "rel" on this link tag is "http://api.friendfeed.com/2008/03#sup"
    RSS feeds need to include the Atom namespace on the link tag.

    Ideally, feeds that include the SUP tag should also set the HTTP 
    "Vary" header to include "X-SUP-UID" (e.g "Vary: X-SUP-UID").
    Clients refreshing the feed in response a SUP entry should then
    include the HTTP header "X-SUP-UID: <update_id>" where "<update_id>"
    is the update_id from the SUP entry that triggered the feed fetch.
    This is to avoid the problem of an intermediate HTTP cache serving
    an older version of the feed which does not include the latest update.
    If the server does not include the "Vary" header, then clients can
    instead use the HTTP header "Cache-Control: max-age=0" when refreshing
    the feed.

    Side Note: SUP can be extended to work for all HTTP GET requests,
    regardless of content, by putting the SUP feed url and SUP-ID in an
    HTTP header, e.g. "X-SUP-ID: http://mysite.com/sup.json#12345"
    Ideally, SUP consumers should watch for both the SUP link tag and
    the X-SUP-ID HTTP header.
    """
    sup_feed = "http://mysite.com/sup.json"  # your site
    sup_id = generate_sup_id(username)
    ns = 'xmlns="http://www.w3.org/2005/Atom" ' if for_rss else ""
    return \
        '<link %srel="http://api.friendfeed.com/2008/03#sup" href="%s#%s" type="application/json"/>' \
        % (ns, sup_feed, sup_id)

def make_sup_json(updated, since, period, updates):
    """ 
    The sup json has the following structure:
        "updated_time": When this data was generated (RFC 3339 time),
        "since_time": All updates are since this time (RFC 3339 time),
        "period": The time period covered by the data (in seconds)
        "available_periods": {
            period: sup_feed_url,
            ...
        },
        "updates": [
            [sup_id, update_id],
            ...
        ]

    The "update_id" is a string used to eliminate duplicate pings. The update
    time works well and is useful when debugging, but in principle anything
    can be used, and consumers should not attempt to parse or interpret it.

    SUP consumers should fetch SUP feeds slightly faster than every "period"
    seconds.

    If a SUP publishers supports multiple time periods, SUP feeds should
    include "available_periods", which is a dictionary from time periods
    (in seconds) to urls. This is optional.
    """
        
    sup_updates = [
        [generate_sup_id(u.username), str(u.updated)]
        for u in updates]    

    return simplejson.dumps({
        "updated_time": rfc_3339_time(updated),
        "since_time": rfc_3339_time(since),
        "period": period,
        "updates": sup_updates
    })

def generate_sup_update(database, period):
    """
    Example code for querying a database in order to generate a sup feed. 

    When serving a SUP feed, the server should set the HTTP "Expires"
    header to updated_time + period, e.g.
    set_header("Expires", update_time + datetime.timedelta(seconds=period))
    """
    update_time = datetime.datetime.utcnow()
    since = update_time - datetime.timedelta(seconds=period)
    updates = database.query(
        "SELECT username, updated FROM users WHERE updated >= %s",
        since)
    return make_sup_json(update_time, since, period, updates)

class DummyDb(object):
    class Result(object):
        pass

    def query(self, q, since):
        results = []
        for i, name in enumerate(['ana', 'bret', 'casey', 'dan']):
            r = DummyDb.Result()
            r.username = name
            r.updated = calendar.timegm(
                (since + datetime.timedelta(seconds=i)).utctimetuple())
            results.append(r)
        return results

def test():
    db = DummyDb()
    print "Link tag for Ana's Atom feed:"
    print "  ", make_sup_link("ana")
    print
    print "Link tag for Ana's RSS feed:"
    print "  ", make_sup_link("ana", for_rss=True)
    print
    print "SUP feed:"
    print "  ", generate_sup_update(db, 120)


    """ Output is:
    Link tag for Ana's Atom feed:
       <link rel="http://api.friendfeed.com/2008/03#sup" href="http://mysite.com/sup.json#276b6c46" type="application/json"/>

    Link tag for Ana's RSS feed:
       <link xmlns="http://www.w3.org/2005/Atom" rel="http://api.friendfeed.com/2008/03#sup" href="http://mysite.com/sup.json#276b6c46" type="application/json"/>

    SUP feed:
       {"since_time": "2008-08-12T01:44:49Z", "period": 120, "updates": [["276b6c46", "1218505489"], ["264400b7", "1218505490"], ["1e21afeb", "1218505491"], ["9180b4da", "1218505492"]], "updated_time": "2008-08-12T01:46:49Z"}
    """

if __name__ == "__main__":
    test()
