# ZwiftPower Profile Change Data

This repo contains code to fetch and analyse rider height and weight change
data from https://www.zwiftpower.com. It doesn't contain any actual data.

The intent is to increase transparancy of stat changes of competitive Zwift
racers, particularly height data, which seems to under recognised as a
performance variable in Zwift racing.

Note that a rider's height/weight changing does not imply they are cheating,
there are a large number of legitimate reasons for changes. For example:
* To allow a friend to try Zwift via their account
* To correct an incorrect value
* To analyse the performance effects of values 

## Background

I threw this code together quickly on the 20th Feb 2019 when I noticed that
ZwiftPower had started publishing height change data (as well as weight changes)
in the "Aliases" section of their rider profiles.

On the 20th the issue of how rider height affects performance in Zwift got some
attention, in particular with Chris Pritchard posting a video on 
[height performance and height doping in Zwift][height-doping-video]. 

As of the 21st Feb 2019 ZwiftPower has stopped showing profile changes for the
last few weeks, so height changes are not currently visible.

[height-doping-video]: https://www.youtube.com/watch?v=w4BI1WwhL8M

## Programs

I'm not documenting this very much so that it requires some technical ability to
use. The following need to be used in order, feeding data between them as
appropriate.

1. `generate-profile-urls.sh`: Create a list of ZwiftPower profile URLs for use
  with aria2.
2. `fetch-profiles.sh`: Download a list of profiles from ZwiftPower to 
  `./profiles/profile_<id>.html`. Takes several hours.
3. `parse-profiles.sh`: Scrape profile change data from the profile HTML,
  producing newline-delimited JSON, one object per profile. This takes a few
  minutes, I guess the HTML parser is quite slow. 
4. `find_profile_changes.py`: Analyse profile JSON to find profiles with unusual
  changes.
  Note that reporting weight changes is not currently implemented, but the
  weight data is available. 
5. `anonymise.py`: Filter a stream of suspicious change description objects from
   `find_profile_changes.py` to remove identifiable features.
