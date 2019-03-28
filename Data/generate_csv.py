import csv,os

with open(r'dataset.csv', mode = 'w') as csv_file:
    csv_writer = csv.writer(csv_file)
    gen = os.walk(os.getcwd())
    main_dirs = next(gen)[1] #2 directories in current folder: A train and a test
    author_list = next(gen)[1]
    while True:
        try:
            for ind in range(len(author_list)): #Iterating through generator - Visiting each author subdirectory
                item = next(gen)
                path = item[0]
                files = item[-1]
                for file in files:
                    file_path = os.path.join(path,file)
                    with open(file_path,mode = 'r') as read_file:
                        text = read_file.read()
                        csv_writer.writerow([author_list[ind],text])
            item = next(gen) #Generates same tuple as line 3

        except StopIteration:
            break
                        
