# OBS Avatar Setup Guide

The chatbot creates a file called `current_avatar.png` in the project directory that automatically switches between your speaking and idle images.

## Setup in OBS:

1. **Add Image Source**
   - In OBS, click the + button in Sources
   - Select "Image"
   - Name it "AI Avatar" or whatever you prefer

2. **Select the Avatar File**
   - Click "Browse"
   - Navigate to your chatbot folder
   - Select `current_avatar.png`

3. **Enable Auto-Refresh** (IMPORTANT)
   - Check the box "Unload image when not showing"
   - This makes OBS reload the file when it changes

4. **Position & Resize**
   - Drag and resize the image source in your OBS preview
   - Position wherever you want on your stream layout

5. **Test It**
   - Start the chatbot
   - The avatar should appear as your idle image
   - When the AI speaks, it should switch to the speaking image
   - When done speaking, it switches back to idle

## Tips:

- The image updates automatically - no need to refresh OBS
- You can add filters/effects to the image source in OBS
- Works great with green screen if your images have transparency
- Position it over your game/content where you want the avatar visible