#summary Frequently asked questions about SUP

# SUP FAQ #

### What is SUP? ###
SUP (Simple Update Protocol) is a simple and compact "ping feed" that web services can produce in order to alert the
consumers of their feeds when a feed has been updated. This reduces update latency and improves efficiency by eliminating
the need for frequent polling.

### How is SUP different from existing ping services? ###
Traditional ping services require feed publishers to ping one or more centralized ping services every time one of their
feeds is updated. This is inappropriate for large services that may have thousands or millions of feeds, and is rarely utilized
for anything other than blogs. Furthermore, there is no way to know which, if any, ping services are updated by any given feed
(it is not discoverable). Also, since ping services are based on feed urls, they can not be used for services, such as Google
Reader, which do not wish to publicly expose all of their feed urls.

SUP solves these problems by providing an open, discoverable, and standardized way for feed providers to share pings. Since
it's based on opaque tokens known as "SUP-IDs", publishers do not have to reveal any additional information, and updates
can be extremely compact (about 21 bytes each, or 8 bytes with gzip encoding). There is no central ping server, so SUP
is practical for both large and small publishers, and everyone has open and equal access to the update information.

### Why not use use some kind of push oriented or streaming protocol such as XMPP or the Six Apart Update Stream? ###
SUP has been designed to make life as easy as possible for feed publishers. Since it is based on simple HTTP
and requires no special libraries, it can easily and efficiently be implemented in almost any environment or language.
For example, <a href='http://laconi.ca/'>Laconica</a>/<a href='http://identi.ca/'>Identica</a> implemented SUP in
about <a href='http://github.com/zh/laconica/tree/master/actions/sup.php'>45 lines of PHP code</a> (plus
<a href='http://github.com/zh/laconica/tree/master/actions/userrss.php'>2 lines</a> to add the necessary HTTP header).
SUP does not require streaming HTTP libraries or long lived HTTP connections (which are difficult with many hosting environments),
and it does not send a lot of unnecessary data (since it includes only a minimal ID instead of the full Atom content).

Once feed publishers make this information available via SUP, then other people can build additional services that
translate updates into HTTP callbacks, XMPP, email, or any other protocol desired by feed consumers. However, if feed
publishers do not share this information at all, then none of these other services would be possible. Therefore, SUP
is designed primarily around the needs of feed publishers, with the goal of maximizing the number of SUP-enabled feeds.


### Why not send all updates to a centralized service which can then redistribute them to feed consumers? ###
This approach would create unnecessary bottlenecks, single-points-of-failure, and would give one (or a small number)
of services a privileged role. We believe in creating an open Internet where everyone has equal access to information.
If someone decides to create a new FriendFeed-like product, that person should have the same access to feeds and updates
that FriendFeed has. SUP provides that equal access by making updates available as a standard, discoverable HTTP resource
accessible by anyone.


### Why does SUP use SUP-IDs instead of URLs or URL-fingerprints? ###
For a variety of reasons, including the desire to guard private or competitive data, many feed publishers do not wish
to publish a complete list of feed urls. SUP-IDs allow them to instead assign an arbitrary string of letters and numbers
to identify each feed. The only way to discover a feed's SUP-ID is by downloading the feed, therefore no additional information
is revealed by a SUP-ID. SUP-IDs can also be much shorter than URLS (the SUP-IDs used by friendfeed.com are only 8 bytes),
which is important on busy sites that have a high update rate.

Keeping with the philosophy of making life simple for feed publishers, SUP-IDs are arbitrary, and feed publishers
are free to decide how they should be assigned. One of the benefits of generating SUP-IDs based on something internal,
such as user-ids, is that it feed publishers can assign the same SUP-ID to multiple urls. For example
<a href='http://friendfeed.com/paul?format=atom'><a href='http://friendfeed.com/paul?format=atom'>http://friendfeed.com/paul?format=atom</a></a>,
<a href='http://friendfeed.com/api/feed/user/paul?format=rss'><a href='http://friendfeed.com/api/feed/user/paul?format=rss'>http://friendfeed.com/api/feed/user/paul?format=rss</a></a>, and
<a href='http://friendfeed.com/api/feed/user/paul?format=json&pretty=1'><a href='http://friendfeed.com/api/feed/user/paul?format=json&pretty=1'>http://friendfeed.com/api/feed/user/paul?format=json&amp;pretty=1</a></a>
all have the same SUP-ID (53924729) because they all represent the same underlying feed (but with different formats and options).
This technique also means that we do not have to worry about URL canonicalization issues such as escaping and encoding, whether the
hostname starts with "www", etc.

However, keeping with the philosophy of making life simple for feed publishers, SUP-IDs MAY be URL hashes, but this decision
is left up to the feed publisher, and feed consumers should never make any assumption about the method used to assign SUP-IDs.


### Is SUP appropriate for people who only publish a small number of feeds, such as an individual blog? ###
Since SUP works by aggregating update information (or "pings") for a large number of feeds into a single SUP feed,
it does not make sense to create a SUP feed for a single RSS or Atom feed. Fortunately, feed providers can easily delegate
to a shared SUP feed hosted elsewhere.

To make it easy for small publishers to add support for SUP, FriendFeed now offers a
<a href='http://friendfeed.com/api/public-sup'>public SUP feed</a> which anyone can use to publish updates. Although this shared SUP feed
is provided by FriendFeed, it can easily be replicated by other services, the data is freely available,
and feed publishers could easily switch to other shared SUP feeds, so there is no lock-in to the FriendFeed service.

Benjamin Golub's simple, open-source blog software
<a href='http://github.com/bgolub/blog/commit/1c700dcff649efdf6d675714eb278370e04cf902'>provides a great example</a>
of how this can be used to to add SUP support with only a few lines of code.


### Is there a validator so that I can verify that my SUP feed is well-formed? ###
Yes, <a href='http://friendfeed.com/api/sup-validator'>it is available here</a>.
The <a href='http://code.google.com/p/simpleupdateprotocol/source/browse/trunk/validatesup.py'>source code</a> for this validator is also freely available.


### How do RSS and Atom feeds reveal their SUP-ID and SUP feed? What about other content types? ###
Feeds can either include the "X-SUP-ID" HTTP header
(e.g. `X-SUP-ID: http://friendfeed.com/api/public-sup.json#SUP-ID`)
or the SUP-ID link tag
(e.g.  `<link rel="http://api.friendfeed.com/2008/03#sup" xmlns="http://www.w3.org/2005/Atom" type="application/json" href="http://friendfeed.com/api/public-sup.json#SUP-ID">`), or both.

The HTTP header is preferable since it works for all content types (not just RSS and Atom feeds), but either method is acceptable.
See <a href='http://friendfeed.com/rooms/friendfeed-news?format=atom'><a href='http://friendfeed.com/rooms/friendfeed-news?format=atom'>http://friendfeed.com/rooms/friendfeed-news?format=atom</a></a> for an example of a SUP-enabled feed.


### How can I check if I have correctly added SUP to my feeds? ###
The FriendFeed <a href='http://friendfeed.com/api/feedtest'>RSS/Atom feed tester</a> shows what, if any, SUP-ID is associated with a feed.


### What is the right value for the "period" field is SUP? ###
"period" specifies the default polling period for a SUP feed, in seconds. 60 seconds is a good default, though it's best
to make multiple intervals available using the optional "available\_periods" property. See
<a href='http://friendfeed.com/api/sup.json?pretty=1'>FriendFeed's SUP feed</a> for an example.


### Why not use a bloom filter? ###
A <a href='http://en.wikipedia.org/wiki/Bloom_filter'>bloom filter</a> would be much more complex to specify and implement (it's not the sort of thing that can be done in a few
lines of PHP). SUP is already very compact, especially when using standard HTTP gzip encoding, so the savings would not be
significant in most cases. That said, it would be straightforward to create a bloom-filter variant of SUP where the
SUP-IDs are keys into the bloom filter. This and other potential SUP extensions could be discovered via the standard SUP
feeds, so these variants would not be incompatible with the existing SUP standard.


### Is there example source code? ###
Yes. <a href='http://laconi.ca/'>Laconica</a>/<a href='http://identi.ca/'>Identica</a> is open source and
has implmemented full SUP support in about <a href='http://github.com/zh/laconica/tree/master/actions/sup.php'>45 lines of PHP code</a> (plus
<a href='http://github.com/zh/laconica/tree/master/actions/userrss.php'>2 lines</a> to add the necessary HTTP header).

Benjamin Golub's simple, open-source blog software uses
<a href='http://friendfeed.com/api/public-sup'>FriendFeed's public SUP feed</a> to add SUP support
with only <a href='http://github.com/bgolub/blog/commit/1c700dcff649efdf6d675714eb278370e04cf902'>a few lines of Python</a>.

We also provide
<a href='http://code.google.com/p/simpleupdateprotocol/source/browse/trunk/supintro.py'>heavily commented sample code</a>
as part of the SUP documentation.
