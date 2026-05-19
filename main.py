from Crawler import main as crawl_main
from Cleaner import main as clean_main
from Aggregator import main as aggregate_main
from Classify import main as classify_main


def main():
    print("STEP 1: Crawl")
    crawl_main()
    print("STEP 2: Aggregate")
    aggregate_main()
    print("STEP 3: Clean")
    clean_main()
    print("STEP 4: Classify")
    classify_main()

if __name__ == "__main__":
    main()
