#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of AudioLazy, the signal processing Python package.
# Copyright (C) 2012-2013 Danilo de Jesus da Silva Bellini
#
# AudioLazy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Created on Tue Mar 05 2013
# danilo [dot] bellini [at] gmail [dot] com
"""
Pitch follower via zero-crossing rate with Tkinter GUI
"""

# ------------------------
# AudioLazy pitch follower
# ------------------------
from audiolazy import (tostream, zcross, lag_to_freq, AudioIO, freq2str, sHz,
                       lowpass)

@tostream
def zcross_pitch(sig, size=2048, hop=None):
  for blk in zcross(sig, hysteresis=.2).blocks(size=size, hop=hop):
    crossings = sum(blk)
    yield 0. if crossings == 0 else lag_to_freq(2. * size / crossings)


def pitch_from_mic(upd_time_in_ms):
  rate = 44100
  s, Hz = sHz(rate)

  with AudioIO() as recorder:
    snd = recorder.record(rate=rate)
    sndlow = lowpass(400 * Hz)(snd)
    hop = int(upd_time_in_ms * 1e-3 * s)
    for pitch in freq2str(zcross_pitch(sndlow, size=2*hop, hop=hop) / Hz):
      yield pitch


# ----------------
# GUI with Tkinter
# ----------------
if __name__ == "__main__":
  import Tkinter
  import threading
  import re

  # Window (Tk init), text label and button
  tk = Tkinter.Tk()
  tk.title(__doc__.strip().splitlines()[0])
  lbldata = Tkinter.StringVar(tk)
  lbltext = Tkinter.Label(tk, textvariable=lbldata)
  lbltext.pack(expand=True, fill=Tkinter.BOTH)
  btnclose = Tkinter.Button(tk, text="Close", command=tk.destroy,
                            default="active")
  btnclose.pack(fill=Tkinter.X)

  # Needed data
  regex_note = re.compile(r"^([A-Gb#]*-?[0-9]*)([?+-]?)(.*?%?)$")
  upd_time_in_ms = 200

  # Update functions for each thread
  def upd_value(): # Recording thread
    pitches = iter(pitch_from_mic(upd_time_in_ms))
    while not tk.should_finish:
      tk.value = pitches.next()

  def upd_timer(): # GUI mainloop thread
    lbldata.set("\n".join(regex_note.findall(tk.value)[0]))
    tk.after(upd_time_in_ms, upd_timer)

  # Multi-thread management initialization
  tk.should_finish = False
  tk.value = freq2str(0) # Starting value
  lbldata.set(tk.value)
  tk.upd_thread = threading.Thread(target=upd_value)

  # Go
  tk.upd_thread.start()
  tk.after_idle(upd_timer)
  tk.mainloop()
  tk.should_finish = True
  tk.upd_thread.join()
