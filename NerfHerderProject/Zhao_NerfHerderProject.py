import os

def Funct1(): # Calculating the sentiment score of a single word from the user using movie reviews

    myFile = open("movieReviews.txt")
    theWordForF1 = input("Enter a word: ").lower()
    counter = 0
    score = 0
    for lines in myFile:
        lines = lines.split()
        for i in range(len(lines)):
            lines[i] = lines[i].lower()
        if theWordForF1 in lines[1:] :
            counter += 1
            score += int(lines[0])
    myFile.close()

    if counter != 0:
        print(f"\"{theWordForF1}\" appears {counter} times as a whole word comparison.")
        average = score/counter
        print(f"The average score for reviews containing {theWordForF1} is {average:0.2f}")
    if counter == 0:
        print("The word you have given does not appear in the file at all.")


def Funct2(): # Calculating the average sentiment score of the words in an input file using movie reviews
    File = input("Enter the name of the file with the words: ")
    openedFile = open(File)
    listOfWordsScores = []
    JustMoveOn = 0
    for lines1 in openedFile:
        lines1 = lines1.split()
        for words in range(len(lines1)):
            lines1[words] = lines1[words].lower()
            myFile = open("movieReviews.txt")
            counter = 0
            score = 0
            average = 0
            for lines2 in myFile:
                lines2 = lines2.split()
                for w in range(len(lines2)):
                    lines2[w] = lines2[w].lower()
                if lines1[words] in lines2[1:] :
                    counter += 1
                    score += int(lines2[0])
            if counter == 0:
                JustMoveOn += 1
            else:
                average = score/counter
                listOfWordsScores.append(average)
                myFile.close()

    finalTotalScores = 0
    for n in range(len(listOfWordsScores)) :
        listOfWordsScores[n] = float(listOfWordsScores[n])
        finalTotalScores += listOfWordsScores[n]
    finalAverage = (finalTotalScores/len(listOfWordsScores))
    cutFinalAverage = f"{finalAverage:0.2f}"
    cutFinalAverage = float(cutFinalAverage)
    if cutFinalAverage < 1.75:
        print(f"The average score of the words in {File} is {cutFinalAverage}. This is an insult.")
    elif cutFinalAverage > 2.25:
        print(f"The average score of the words in {File} is {cutFinalAverage}. This is a compliment.")
    else:
        print(f"The average score of the words in {File} is {cutFinalAverage}. This is not a compliment nor an insult.")

    openedFile.close()

def Funct3(): # Finding the highest and lowest scoring words in a file using movie reviews
    File = input("Enter the name of the file with the words: ")
    openedFile = open(File)
    listOfWordsScores = []
    fakeMax = 1234567890
    for lines1 in openedFile:
        lines1 = lines1.split()
        for words in range(len(lines1)):
            lines1[words] = lines1[words].lower()
            myFile = open("movieReviews.txt")
            counter = 0
            score = 0
            average = 0
            for lines2 in myFile:
                lines2 = lines2.split()
                for w in range(len(lines2)):
                    lines2[w] = lines2[w].lower()
                if lines1[words] in lines2[1:] :
                    counter += 1
                    score += int(lines2[0])
            if counter == 0:
                listOfWordsScores.append("notfound")
            else:
                average = score/counter
                listOfWordsScores.append(average)
                myFile.close()
    openedFile.close()

    for i in range(len(listOfWordsScores)):
        if listOfWordsScores[i] == "notfound":
            listOfWordsScores[i] = fakeMax
    RealMin = min(listOfWordsScores)
    for i in range(len(listOfWordsScores)):
        if listOfWordsScores[i] == fakeMax :
            listOfWordsScores[i] = 0
    RealMax = max(listOfWordsScores)

    indexOfMin = listOfWordsScores.index(RealMin)
    indexofMax = listOfWordsScores.index(RealMax)

    openedFile2nd = open(File)

    giantStr = openedFile2nd.read()
    giantStr = giantStr.split()

    minWord = giantStr[indexOfMin]
    maxWord = giantStr[indexofMax]

    print(f"The most positive word in {File} is {maxWord} with a score of {RealMax:0.2f}")
    print(f"The most negative word in {File} is {minWord} with a score of {RealMin:0.2f}")

def main(): #  Asks the user to pick 1 out of the 4 options, 3 of which are the functions
                # I defined previously and the last option is to exit the code.


    cwd = os.getcwd()       #change the file location so that text files such as movieReviews.txt and word.txt is visible 

    changeDirectory = cwd+ "\\NerfHerderProject"

    os.chdir(changeDirectory)



    userinput = 0
    while userinput != 4:
        userinput = input("""
What would you like to do?
1.  Calculate the sentiment score of a single word
2.  Calculate the average score of words in a file
3.  Find the highest and lowest scoring words in a file.
4.  Exit the program
Enter a number 1-4: """)

        userinput = int(userinput)  

        if userinput == 1:
            Funct1()
        elif userinput == 2:
            Funct2()
        elif userinput == 3:
            Funct3()
        elif userinput == 4:
            print("I hope you liked my project!")
        else:
            print("please input a number from 1 through 4")
main()

            
    
