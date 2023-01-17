from pebble import ProcessPool
from queue import Queue
import gpt

def pray(q, uuid, flashcards, openended, mcq, summary):
    result_queue = []
    with ProcessPool(max_workers=4) as pool:
        future = Queue()
        
        if openended:
            future.put((pool.schedule(gpt.generateQuiz, args=(q,)), ["openendedArray", uuid]))
        if mcq:
            future.put((pool.schedule(gpt.generateMCQ, args=(q,)), ["mcqArray", uuid]))
        if flashcards:
            future.put((pool.schedule(gpt.generateFlashcards, args=(q,)), ["flashcardsArray", uuid]))
        if summary:
            future.put((pool.schedule(gpt.generateSummary, args=(q,)), ["summaryResult", uuid]))
        
        print("future", future.qsize())

        while future.empty() is False:
            try:
                res = future.get()
                result = res[0].result()
                metadata = res[1]
                assert result != None
                
                result_queue.append([result, metadata])
            except TimeoutError:
                print("Ayo GPT took too long >:(")
    return result_queue