import random
from graphics import *


PicWidth = 900
PicHeight = 900

# actually draws the rectangles
def rects(firstX,firstY,secondX,secondY,win): 
    aRect = Rectangle(Point(firstX,firstY), Point(secondX,secondY))
    aRect.setOutline("black")
    aRect.setFill("white") 
    aRect.draw(win)

# colors in the rectangles
def paint(): 
    r = random.uniform(0,1)
    if r < 0.09:
        color = "yellow"
    elif r < 0.15:
        color = "blue"
    elif r < 0.25:
        color = "red"
    else:
        color = "white"
    return color
    
# Everything named th3rdpercentile and six8percentile represents the 31st percentile and the 68th percentile of the region and the split
    # that may or may not be happening in that region must happen in between the percentiles.

# splits the region horizontally and vertically
def splitVAndH(firstX,firstY,secondX,secondY,win):
    th3rdpercentileX = (firstX+0.31*(secondX-firstX))
    six8percentileX = (firstX+0.68*(secondX-firstX))
    th3rdpercentileX = int(th3rdpercentileX)
    six8percentileX = int(six8percentileX)

    widthsplit = random.randrange(th3rdpercentileX, six8percentileX)

    th3rdpercentileY = (firstY+0.31*(secondY-firstY))
    six8percentileY = (firstY+0.68*(secondY-firstY))
    th3rdpercentileY = int(th3rdpercentileY)
    six8percentileY = int(six8percentileY)

    heightsplit = random.randrange(th3rdpercentileY, six8percentileY)

    rects(firstX,firstY,widthsplit,heightsplit,win)
    rects(widthsplit,firstY,secondX,heightsplit,win)
    rects(firstX,heightsplit,widthsplit,secondY,win)
    rects(widthsplit,heightsplit,secondX,secondY,win)

    drawArt(firstX,firstY,widthsplit,heightsplit,win)
    drawArt(widthsplit,firstY,secondX,heightsplit,win)
    drawArt(firstX,heightsplit,widthsplit,secondY,win)
    drawArt(widthsplit,heightsplit,secondX,secondY,win)

# splits the region vertically
def splitVert(firstX,firstY,secondX,secondY,win):
    th3rdpercentileX = (firstX+0.31*(secondX-firstX))
    six8percentileX = (firstX+0.68*(secondX-firstX))
    th3rdpercentileX = int(th3rdpercentileX)
    six8percentileX = int(six8percentileX)
    widthsplit = random.randrange(th3rdpercentileX, six8percentileX)

    rects(firstX,firstY,widthsplit,secondY,win)
    rects(widthsplit,firstY,secondX,secondY,win)

    drawArt(firstX,firstY,widthsplit,secondY,win)
    drawArt(widthsplit,firstY,secondX,secondY,win)

# splits the region horizontally
def splitHori(firstX,firstY,secondX,secondY,win):
    th3rdpercentileY = (firstY+0.31*(secondY-firstY))
    six8percentileY = (firstY+0.68*(secondY-firstY))
    th3rdpercentileY = int(th3rdpercentileY)
    six8percentileY = int(six8percentileY)
    heightsplit = random.randrange(th3rdpercentileY, six8percentileY)

    rects(firstX,firstY,secondX,heightsplit,win)
    rects(firstX,heightsplit,secondX,secondY,win)

    drawArt(firstX,firstY,secondX,heightsplit,win)
    drawArt(firstX,heightsplit,secondX,secondY,win)




# examines the region being given in the parameters and decide how to split it.
def drawArt(firstX,firstY,secondX,secondY,win):
    if (secondX-firstX) > PicWidth/2 and (secondY-firstY) > PicHeight/2 :
        splitVAndH(firstX,firstY,secondX,secondY,win)
    else:
        if (secondX-firstX) > PicWidth/2 :
            splitVert(firstX,firstY,secondX,secondY,win)
        if (secondY-firstY) > PicHeight/2 :
            splitHori(firstX,firstY,secondX,secondY,win)
        else:
            if 90 < (secondX-firstX) and 90 < (secondY-firstY):
                maybeSplitVert = random.randint(90,int((secondX-firstX)*1.5))
                maybeSplitHori = random.randint(90,int((secondY-firstY)*1.5))
                
                if maybeSplitVert < (secondX-firstX) and maybeSplitHori < (secondY-firstY):
                    splitVAndH(firstX,firstY,secondX,secondY,win)
                else:
                    if maybeSplitVert < (secondX-firstX):
                        splitVert(firstX,firstY,secondX,secondY,win)
                    if maybeSplitHori < (secondY-firstY):
                        splitHori(firstX,firstY,secondX,secondY,win)
            else:
                if 90 < (secondX-firstX) < PicWidth/2:
                    maybeSplitVert = random.randint(90,int((secondX-firstX)*1.5))

                    if maybeSplitVert < (secondX-firstX):
                        splitVert(firstX,firstY,secondX,secondY,win)
                if 90 < (secondY-firstY) < PicHeight/2:
                    maybeSplitHori = random.randint(90,int((secondY-firstY)*1.5))

                    if maybeSplitHori < (secondY-firstY):
                        splitHori(firstX,firstY,secondX,secondY,win)
                else:
                    aRect = Rectangle(Point(firstX,firstY), Point(secondX,secondY))
                    aRect.setOutline("black")
                    aRect.setFill(paint())
                    aRect.draw(win)
            


def main():
    win = GraphWin("I'm an Artist!", PicWidth, PicHeight)
    drawArt(0,0,PicWidth,PicHeight,win)
    win.getMouse()
    win.close()

main()

