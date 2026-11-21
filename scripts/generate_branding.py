"""Generate native branding assets from the website's simple waveform geometry."""
import _bootstrap
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parents[1]
ORANGE = '#f26036'
CREAM = '#fffaf3'

def logo(size):
    scale = size / 40
    image = Image.new('RGBA', (size, size))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, size-1, size-1), radius=11*scale, fill=ORANGE)
    for x, y1, y2 in [(10,17,23),(15,12,28),(20,9,31),(25,14,26),(30,18,22)]:
        draw.rounded_rectangle(((x-1.5)*scale,(y1-1.5)*scale,(x+1.5)*scale,(y2+1.5)*scale),radius=1.5*scale,fill=CREAM)
    return image

if __name__ == '__main__':
    icon = logo(256)
    icon.save(ROOT/'assets/app.ico', sizes=[(s,s) for s in (16,24,32,48,64,128,256)])
    icon.save(ROOT/'website/dist/favicon.ico', sizes=[(s,s) for s in (16,32,48)])
    small = Image.new('RGB',(55,55),CREAM)
    small.paste(logo(45),(5,5),logo(45))
    small.save(ROOT/'packaging/wizard-small.bmp')
    panel = Image.new('RGB',(164,314),'#faf8f2')
    panel.paste(logo(100),(32,40),logo(100))
    d=ImageDraw.Draw(panel)
    d.rounded_rectangle((22,185,142,191),radius=3,fill=ORANGE)
    d.rounded_rectangle((38,204,126,210),radius=3,fill='#f1b48c')
    d.rounded_rectangle((54,223,110,229),radius=3,fill='#f1b48c')
    panel.save(ROOT/'packaging/wizard.bmp')
