# -*- coding: utf-8 -*-

import math
import random
import re
import threading

from util import hook


def sanitize(s):
    return re.sub(r'[\x00-\x1f]', '', s)

def picmunge(inp, picmunge_count=0):
    reps = 0
    for n in xrange(len(inp)):
        rep = character_replacements.get(inp[n])
        if rep:
            inp = inp[:n] + rep.decode('utf8') + inp[n + 1:]
            reps += 1
            if reps == picmunge_count:
                break
    return inp


class PaginatingWinnower(object):

    def __init__(self):
        self.lock = threading.Lock()
        self.last_input = []
        self.recent = set()

    def winnow(self, inputs, limit=400, ordered=False):
        "remove random elements from the list until it's short enough"
        with self.lock:
            # try to remove elements that were *not* removed recently
            inputs_sorted = sorted(inputs)
            if inputs_sorted == self.last_input:
                same_input = True
            else:
                same_input = False
                self.last_input = inputs_sorted
                self.recent.clear()

            combiner = lambda l: u', '.join(l)
            suffix = ''

            while len(combiner(inputs)) >= limit:
                if same_input and any(inp in self.recent for inp in inputs):
                    if ordered:
                        for inp in self.recent:
                            if inp in inputs:
                                inputs.remove(inp)
                    else:
                        inputs.remove(
                            random.choice([inp for inp in inputs if inp in self.recent]))
                else:
                    if ordered:
                        inputs.pop()
                    else:
                        inputs.pop(random.randint(0, len(inputs) - 1))
                suffix = ' ...'

            self.recent.update(inputs)
            return combiner(inputs) + suffix

winnow = PaginatingWinnower().winnow


def add_pic(db, chan, nick, subject):

    match = db.execute('select * from pic where lower(nick)=lower(?) and'
                       ' chan=? and lower(subject)=lower(?)',
                       (nick, chan, subject)).fetchall()
    if match:
        return 'already picced'
    if not ".jpg" in subject:
        if not ".png" in subject:
            if not ".gif" in subject:
                return 'THATS NOT A PIC'
   
    db.execute('replace into pic(chan, subject, nick) values(?,?,?)',
               (chan, subject, nick))

    db.commit()
    return 'pic added'

def delete_pic(db, chan, nick, del_pic):
    count = db.execute('delete from pic where lower(nick)=lower(?) and'
                       ' chan=? and lower(subject)=lower(?)',
                       (nick, chan, del_pic)).rowcount
    db.commit()

    if count:
        return 'deleted'
    else:
        return 'pic not found'


def get_pic_counts_by_chan(db, chan):
    pics = db.execute("select subject, count(*) from pic where chan=?"
                      " group by lower(subject)"
                      " order by lower(subject)", (chan,)).fetchall()

    pics.sort(key=lambda x: x[1], reverse=True)
    if not pics:
        return 'no pics in %s' % chan
    return winnow(['%s (%d)' % row for row in pics], ordered=True)


def get_pics_by_nick(db, chan, nick):
    pics = db.execute("select subject from pic where lower(nick)=lower(?)"
                      " and chan=?"
                      " order by lower(subject)", (nick, chan)).fetchall()
    if pics:
        return 'pics for "%s": ' % picmunge(nick, 1) + winnow([
            pic[0] for pic in pics])
    else:
        return ''


def get_nicks_by_picset(db, chan, picset):
    nicks = None
    for pic in picset.split('&'):
        pic = pic.strip()

        current_nicks = db.execute("select nick from pic where " +
                                   "lower(subject)=lower(?)"
                                   " and chan=?", (pic, chan)).fetchall()

        if not current_nicks:
            return "pic '%s' not found" % pic

        if nicks is None:
            nicks = set(current_nicks)
        else:
            nicks.intersection_update(current_nicks)

    nicks = [munge(x[0], 1) for x in sorted(nicks)]
    if not nicks:
        return 'no nicks found with picss "%s"' % picset
    return 'nicks picced "%s": ' % picset + winnow(nicks)


@hook.command
def pic(inp, chan='', db=None):
    '.pic <nick> <pic> -- marks <nick> as <pic>'

    db.execute('create table if not exists pic(chan, subject, nick)')

    add = re.match(r'(\S+) (.+)', inp)

    if add:
        nick, subject = add.groups()
        if nick.lower() == 'list':
            return 'pic syntax has changed. try .pics or .picced instead'
        elif nick.lower() == 'del':
            return 'pic syntax has changed. try ".unpic %s" instead' % subject
        return add_pic(db, chan, sanitize(nick), sanitize(subject))
    else:
        pics = get_pics_by_nick(db, chan, inp)
        if pics:
            return pics
        else:
            return pic.__doc__


@hook.command
def unpic(inp, chan='', db=None):
    '.unpic <nick> <pic> -- unmarks <nick> as <pic> {related: .pic, .pics, .picced}'

    delete = re.match(r'(\S+) (.+)$', inp)

    if delete:
        nick, del_pic = delete.groups()
        return delete_pic(db, chan, nick, del_pic)
    else:
        return unpic.__doc__


@hook.command
def pics(inp, chan='', db=None):
    '.pics <nick>/list -- get list of pics for <nick>, or a list of pics {related: .pic, .unpic, .picced}'
    if inp == 'list':
        return get_pic_counts_by_chan(db, chan)

    pics = get_pics_by_nick(db, chan, inp)
    if pics:
        return pics
    else:
        return get_nicks_by_picset(db, chan, inp)


@hook.command
def picced(inp, chan='', db=None):
    '.picced <pic> [& pic...] -- get nicks marked as <pic> (separate multiple pics with &) {related: .pic, .unpic, .pics}'

    return get_nicks_by_picset(db, chan, inp)


@hook.command(autohelp=False)
def picnear(inp, nick='', chan='', db=None):
    try:
        loc = db.execute("select lat, lon from location where chan=? and nick=lower(?)",
                (chan, nick)).fetchone()
    except db.OperationError:
        loc = None

    if loc is None:
        return 'use .weather <loc> first to set your location'

    lat, lon = loc

    db.create_function('distance', 4, distance)
    picnearby = db.execute("select nick, distance(lat, lon, ?, ?) as dist from location where chan=?"
                        " and nick != lower(?) order by dist limit 20", (lat, lon, chan, nick)).fetchall()

    in_miles = 'mi' in inp.lower()

    out = '(km) '
    factor = 1.0
    if in_miles:
        out = '(mi) '
        factor = 0.621

    while picnearby and len(out) < 200:
        nick, dist = picnearby.pop(0)
        out += '%s:%.0f ' % (munge(nick, 1), dist * factor)

    return out


character_replacements = {
    'a': 'ä',
#    'b': 'Б',
    'c': 'ċ',
    'd': 'đ',
    'e': 'ë',
    'f': 'ƒ',
    'g': 'ġ',
    'h': 'ħ',
    'i': 'í',
    'j': 'ĵ',
    'k': 'ķ',
    'l': 'ĺ',
#    'm': 'ṁ',
    'n': 'ñ',
    'o': 'ö',
    'p': 'ρ',
#    'q': 'ʠ',
    'r': 'ŗ',
    's': 'š',
    't': 'ţ',
    'u': 'ü',
#    'v': '',
    'w': 'ω',
    'x': 'χ',
    'y': 'ÿ',
    'z': 'ź',
    'A': 'Å',
    'B': 'Β',
    'C': 'Ç',
    'D': 'Ď',
    'E': 'Ē',
#    'F': 'Ḟ',
    'G': 'Ġ',
    'H': 'Ħ',
    'I': 'Í',
    'J': 'Ĵ',
    'K': 'Ķ',
    'L': 'Ĺ',
    'M': 'Μ',
    'N': 'Ν',
    'O': 'Ö',
    'P': 'Р',
#    'Q': 'Ｑ',
    'R': 'Ŗ',
    'S': 'Š',
    'T': 'Ţ',
    'U': 'Ů',
#    'V': 'Ṿ',
    'W': 'Ŵ',
    'X': 'Χ',
    'Y': 'Ỳ',
    'Z': 'Ż'}
