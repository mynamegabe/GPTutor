rsp = """
1. What is Shor's Algorithm?
a) A quantum computer algorithm for finding the prime factors of an integer
b) A classical computer algorithm for finding the prime factors of an integer
c) A quantum computer algorithm for solving the traveling salesman problem
d) A classical computer algorithm for solving the travelling salesman problem
Answer: a) A quantum computer algorithm for finding the prime factors of an integer

2. How does Shor's Algorithm compare to the most efficient known classical factoring algorithm?
a) It is exponentially slower
b) It is almost exponentially faster
c) It is the same
d) It depends on the size of the input integer
Answer: b) It is almost exponentially faster

3. What is the complexity class of Shor's Algorithm?
a) P
b) NP
c) BQP
d) NP-hard
Answer: c) BQP

4. What public-key cryptography schemes can Shor's Algorithm potentially break?
a) RSA
b) Finite Field Diffie-Hellman key exchange
c) Elliptic Curve Diffie-Hellman key exchange
d) All of the above
Answer: d) All of the above

5. What was the first integer factored using Shor's Algorithm?
a) 15
b) 21
c) 35
d) 50
Answer: a) 15
"""

sections = rsp.split("Answers:")
if len(sections) == 1:
    sections = rsp.split("answers:")
    if len(sections) == 1:
        sections = rsp.split("ANSWERS:")
        if len(sections) == 1:
            sections = rsp.split("Answer:")
            if len(sections) == 1:
                sections = rsp.split("answer:")
if "question" in sections[0]:
    sections.remove(sections[0])
if len(sections) == 2:
    print(sections)
    pass  # Normal
else:
    print("WARNING: FORMAT FOR MCQ WAS NOT GIVEN CORRECTLY, ATTEMPTING TO FIX...")
    print(
        "Assuming Format is of form: \n1. Question\nA) Option 1\nB) Option 2\nC) Option 3\nD) Option 4\nAns: A"
    )
    lines = rsp.split("\n")
    lines = [x.strip() for x in lines if x != ""]  # clean lines
    questions = []
    possible_answers = []
    answers = []
    for question in lines[::6]:
        temp = []
        index_req = lines.index(question)
        questions.append(question[3:])
        for i in range(4):
            temp.append(lines[index_req + i + 1][3:])
        possible_answers.append(temp)
        answers.append(lines[index_req + 5].split(":")[1].strip())

        assert len(answers) == len(questions)
        print("============ QUESTIONS ===================")
        print(questions)
        print("============ POSSIBLE ANSWERS ===================")
        print(possible_answers)
        print("============ ACTUAL ANSWERS ===================")
        print(answers)
        print(
            "RETURN 0: "
            + str(
                [
                    [questions[i], possible_answers[i], answers[i]]
                    for i in range(len(answers))
                ]
            )
        )
qna = sections[0].split("\n")
actualanswers = sections[1]

# Clean the response
qna = [x.strip() for x in qna if x != ""]
# Get Questions and Possible Answers
questions = []
possible_answers = []
for question in qna[::5]:
    temp = []
    index_req = qna.index(question)
    print(index_req)
    questions.append(question[3:])
    for i in range(4):
        temp.append(qna[index_req + i + 1][3:])
    possible_answers.append(temp)

# Get answers
answers = actualanswers.strip().split(", ")
assert len(answers) == len(questions)
print("============ QUESTIONS ===================")
print(questions)
print("============ POSSIBLE ANSWERS ===================")
print(possible_answers)
print("============ ACTUAL ANSWERS ===================")
print(actualanswers)
print(
    "RETURN: "
    + str(
        [[questions[i], possible_answers[i], answers[i]] for i in range(len(answers))]
    )
)
