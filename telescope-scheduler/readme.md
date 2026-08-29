20260829
so about 2 months w/ agy gemini35flash and now gemini37flashhigh where the weekly quota is about 10 minutes of prompts than switch to sonnet46 for another 10 minutes and over that time the models have improved ... earlier got caught in loops that would eat up the week's quota .. now it converges to an answer and corrected code.  By accident the prompts started with darkvader1's stellarium2dwarf app and i didn't bother to change it or restart the prompts clean .. i just added job tabs to the flash page as the weeks wore on... anyway this latest tab is interesting.  It comes from curtis's pre ss50plus youtube where he comments on guiding ... and then i prompt google gemini on the idea:  (paste below, my query started with the co6's starsense guider but the idea is ss50pro wide cam)

=============google gemini chat:
Using a wide-field unit like the Celestron StarSense AutoGuider (SSAG) inside PHD2 changes your guiding scale significantly compared to traditional, narrow-field 50mm or OAG guide scopes. Because the focal length is so short (the SSAG has a 120mm focal length and a large sensor yielding a broad 4° × 3° field of view), each camera pixel covers a much larger slice of the sky. [1, 2, 3]  
To successfully convert and optimize PHD2 for this ultra-wide field configuration, follow this structural guide. 
1. Enable the Proprietary PHD2 Server Loop 
The StarSense AutoGuider contains its own internal computer processing . It does not output a standard ASCOM video stream directly to PHD2 like a basic ZWO or QHY camera. 

• Open Celestron CPWI software. 
• Navigate to the StarSense AutoGuider Settings. 
• Enable "PHD2 Server" mode . This tricks third-party software (like N.I.N.A. or PHD2) into interacting with the SSAG as if it were a native PHD2 source . [2, 6, 7]  

2. Configure the New Profile Wizard 
When setting up your profile in PHD2, you must feed it the exact spatial dynamics of the StarSense lens hardware to avoid massive mathematical calculation errors : 

• Guide Scope Focal Length: Enter exactly 120 mm. 
• Camera Pixel Size:  The SSAG utilizes the Sony IMX178 sensor, which features a pixel size of  2.4 µm. 
• Camera Binning: Set this to 1x1 (Unbinned). Because your focal length is so short, your arcseconds-per-pixel ratio is already very high. Binning further would degrade your spatial resolution too much for accurate centroid calculations. [9, 10, 11]  

3. Adjust Crucial Advanced Brain Settings 
Because your image scale covers more arcseconds per pixel, default PHD2 settings meant for a 200mm+ guide scope will cause sluggish corrections or ignore actual tracking drift. Click the Brain Icon and change the following: [3]  
🧠 Guiding Tab • Use Multi-Star Guiding: Enable this (Check the box). With a massive wide field of view, you will have hundreds of stars available. Guiding on up to 9 stars simultaneously averages out atmospheric seeing distortions, which is vital for short focal lengths. 
• Min Move (Pixels): Lower this to 0.05 – 0.10 pixels. The default (often 0.20) assumes a longer focal length. At 120mm, a 0.20-pixel drift represents a massive physical error on your main imaging camera before PHD2 will even attempt to correct it. [3]  

📷 Camera Tab • Minimum Star HFD: Set this to 1.5 or 2.0 pixels. Wide-field stars focus down into incredibly tight, small point clusters on a 2.4µm sensor. Keeping this low prevents PHD2 from filtering out perfectly sharp stars as noise. 
• Search Region: Set this to 15 or 20 pixels. Because your field of view is wide, stars will not accidentally leave a tight tracking box. A smaller search box speeds up mathematical loop processing times. 

4. Recalibrate and Refine Exposure Time 

• The 2-Second Rule: Set your loop exposure time to 2.0 seconds. Do not use 0.5 or 1.0-second exposures; fast tracking loops will cause a wide-field guider to constantly "chase the seeing" (unproductively over-correcting for rapid atmospheric ripples). 
• Force a Fresh Calibration: Once the hardware profile is active, clear old data by holding  while clicking the Guide button to force a new, highly accurate calibration routine near the celestial equator. [18, 19]  

If you'd like to dial this in further, tell me your main imaging telescope's focal length and what specific mount you are using. This will allow me to check if your pixel-scale ratio is perfectly balanced! 

AI responses may include mistakes.

[1] https://www.youtube.com/watch?v=0f3GokV1pNw
[2] https://www.youtube.com/watch?v=YI4ZzfxuPAY
[3] https://www.cloudynights.com/forums/topic/556913-help-with-phd-and-off-axis-guider-settings/
[4] https://groups.google.com/g/open-phd-guiding/c/vcZ1iYleA7U/m/BPougRyrAwAJ
[5] https://www.youtube.com/watch?v=0f3GokV1pNw
[6] https://www.cloudynights.com/forums/topic/952763-phd2-and-cpwi/
[7] https://www.cloudynights.com/forums/topic/926028-dithering-with-starsense-autoguider/
[8] https://www.youtube.com/watch?v=k1PSfEz2hnU
[9] https://www.youtube.com/watch?v=AnlD0CHdyd4
[10] https://www.cloudynights.com/forums/topic/625343-getting-better-autoguiding-with-phd2/
[11] https://www.reddit.com/r/AskAstrophotography/comments/1rvrak3/phd2_guide_settings/
[12] https://www.youtube.com/watch?v=1gxD7dFkjUo
[13] https://www.youtube.com/watch?v=EX0A01SHvoA
[14] https://www.cloudynights.com/forums/topic/796501-phd2-settings-suggestions-for-oag/
[15] https://www.youtube.com/watch?v=3sTLwqn_tMM
[16] https://www.youtube.com/watch?v=AnlD0CHdyd4
[17] https://www.youtube.com/watch?v=EXGy2RvI6c4
[18] https://www.youtube.com/watch?v=dkm1ePmxWtg
[19] https://openphdguiding.org/man/Advanced_settings.htm

so in the spirt of richard wright's talk guiding_must_die on TAIC
https://www.youtube.com/watch?v=p4bpFJSdHDY
https://youtu.be/p4bpFJSdHDY
and then curtis's piece pre ss50pro that software guiding via the wide angle 2nd cam is possible
https://www.youtube.com/watch?v=rpc6UT-K7tc
https://youtu.be/rpc6UT-K7tc

20260828 i don't know if they updated the default settings or are now making full reference sites a new google ai standard but this is completely different from claude or copilot which will summarize w/ minnimal or no references


anyway the fleet manager still doesn't show the rstp streams on all the scopes .. and as soon as that works w/ the wyze cams i'll post a code dump ... of course i'm kind of embarressed that the first tab is actually darkvader1's app port...but i like having stellarium's visuals..




and the ridiculious pricing by celestron for starsense platesolving and starsense guiders on a CO6 twp pices of equipment i have but could be dup'ed by $100 diy kit strapped to your seestar50 where tracking is "iffy"
