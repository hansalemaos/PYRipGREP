# PYRipGREP
Use the insanely fast regex engine RIPGREP https://github.com/BurntSushi/ripgrep as a python module! Search results are converted directly to dict/numpy/pandas/generator

You can use the class ```python PyRipGREP``` as you would use ripgrep, but you will get a string as result. Because of that I created the class ```python RePatterns ``` where your results are directly converted to dict/numpy/pandas/generator

Check it out:
You'll find the files xaa.txt / xab.txt here: https://github.com/hansalemaos/PYRipGREP/tree/main/textfilesfortests



```python
        outputtype = "np"

        suchennach = ["weniger", "mehr"]

        filetosearch = [
            r"F:\woerterbuecher\wtxt\xaa.txt",
            r"F:\woerterbuecher\wtxt\xab.txt",
        ]
        np_or_df = "np"
        binary = True
        dfa_size = "1G" #Yes, I have a lot of RAM hahaha
        ignore_case = True

        df = RePatterns().find_all_in_files(
            re_expression=suchennach,
            path_to_search=filetosearch,
            outputtype=outputtype,
            binary=binary,
            dfa_size=dfa_size,
            ignore_case=ignore_case,
        )
        print(f"{df=}")

        suchennach = ["sein"]

        df2 = RePatterns().find_all_in_files(
            re_expression=suchennach,
            path_to_search=filetosearch,
            outputtype=outputtype,
            binary=binary,
            dfa_size=dfa_size,
            ignore_case=ignore_case,
        )
        print(f"{df2=}")

        df3 = RePatterns().find_all_in_files(
            re_expression=[r"Buch"],
            path_to_search=filetosearch,
            outputtype=outputtype,
            binary=False,
            dfa_size=dfa_size,
            ignore_case=ignore_case,
        )
        print(f"{df3=}")
        # variable = [
        #     "C:\debugtools\dmpfiles\proddump.dmp",
        #     "C:\debugtools\dmpfiles\procsave2.dmp",
        # ]
        dateistrings = [
            "Das ist ein neues\nHaus Maus Buch",
            "Was kostet das neue Buch?\nBuch Haus Maus",
        ]
        df4 = RePatterns().find_all_in_var_json(
            re_expression=[r"Buch", "Haus"],
            variable=dateistrings[0],
            outputtype=outputtype,
            binary=True,
            ignore_case=True,
        )
        print(f"{df4=}")

        df5 = RePatterns().find_all_in_var(
            re_expression=["mein", r"Buch"],
            variable="Das ist mein Buch. Wo hast du das Buch gekauft?",
            outputtype=outputtype,
            binary=False,
            dfa_size=dfa_size,
            ignore_case=ignore_case,
        )
        print(f"{df5=}")

        df6 = RePatterns().sub_in_files(
            re_expression=[r"Buch", "Haus"],
            repl="Auto",
            path_to_search=filetosearch,
            outputtype=outputtype,
            binary=False,
            dfa_size=dfa_size,
            ignore_case=ignore_case,
        )
        print(f"{df6=}")

        df7 = RePatterns().find_all_in_files_json(
            re_expression=[r"Buch", "Haus"],
            search_in=filetosearch,
            outputtype=outputtype,
            binary=True,
            ignore_case=True,
        )
        print(f"{df7=}")

        df8 = RePatterns().find_all_in_files_json(
            re_expression=[r"Buch", "Haus"],
            search_in=r"F:\nur_df",
            outputtype=outputtype,
            binary=True,
            ignore_case=True,
        )
        print(f"{df8=}")

        text = r"""Guy Reffitt, der am 6. Januar am Sturm aufs US-Kapitol teilnahm, muss für sieben Jahre ins Gefängnis. Der stern hat seine Familie anderthalb Jahre lang begleitet – bis zum Urteil gestern in Washington. Über einen Tag vor Gericht, der Amerikas ganze Verlorenheit offenbart.
    Am Ende ist es eine 18 Jahre junge Frau aus Texas, gerade mit der High School fertig, die den Satz des Tages sagt: "Wenn mein Vater so lange ins Gefängnis muss", sagt sie, "dann verdient Trump lebenslang."
    
    Es ist Peyton Reffitt, die Tochter eines Mannes, der am 6. Januar 2021 am Sturm aufs Kapitol teilnahm. Der stern hat die ganze Familie, die nicht mehr ganz ist, seitdem begleitet. Gestern wurde Peytons Vater, Guy Reffitt, in Washington zu über sieben Jahren Haft verurteilt. Bei niemandem sonst, der am 6. Januar dabei war, fiel das Urteil bisher so hoch aus."""

        df9 = RePatterns().find_all_in_files(
            re_expression=r"\d+\s+\w{5}",
            path_to_search=r"F:\nur_df\wiki0001.txt",
            outputtype=outputtype,
        )
        print(f"{df9=}")
        df10 = RePatterns().find_all_in_files(
            re_expression=r"\d+\s+\w{5}",
            path_to_search=r"F:\nur_df",
            outputtype=outputtype,
        )
        print(f"{df10=}")
        df11 = RePatterns().sub_in_files(
            re_expression=r"\d+\s+(\w{5})",
            repl="$1",
            path_to_search=r"F:\nur_df",
            outputtype=outputtype,
        )
        print(f"{df11=}")
        df12 = RePatterns().find_all_in_var(
            re_expression=r"\d+\.?\s+\w{5}", variable=text, outputtype=outputtype
        )
        print(f"{df12=}")
        df13 = RePatterns().sub_all_in_var(
            re_expression=r"\d+\.?\s+(\w{5})",
            repl="dudu $1",
            variable=text,
            outputtype=outputtype,
        )
        print(f"{df13=}")
        df14 = RePatterns().find_all_in_var_json(
            re_expression=r"\d+\.?\s+(\w{5})", variable=text, outputtype=outputtype
        )
        print(f"{df14=}")

        suchennach = ["Sein"]

    dfxx = RePatterns().find_all_in_files(
        re_expression=r"\w\w[ener]\b",
        path_to_search=r"F:\woerterbuecher\wtxt\xaa.txt",
        outputtype="df",
        binary=True,
        dfa_size="30G",
        ignore_case=True,
    )
    print(f"{dfxx=}")



```


Output: 
```python 
 'df': array([list(['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '15243', '15242', 'Mehr']),
        list(['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '22162', '22161', 'mehr']),
        list(['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '26981', '26980', 'mehr']),
        ...,
        list(['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52397917', '52397916', 'mehr']),
        list(['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52403287', '52403286', 'mehr']),
        list(['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52404523', '52404522', 'mehr'])],
       dtype=object),
 'df2': array([list(['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '4966', '4965', 'sein']),
        list(['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '5021', '5020', 'sein']),
        list(['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '7164', '7163', 'Sein']),
        ...,
        list(['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52415836', '52415835', 'sein']),
        list(['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52420887', '52420886', 'sein']),
        list(['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52422346', '52422345', 'Sein'])],
       dtype=object),
 'df3': array([list(['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '1051', '1050', 'buch']),
        list(['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '28055', '28054', 'buch']),
        list(['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '31815', '31814', 'Buch']),
        ...,
        list(['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52302767', '52302766', 'buch']),
        list(['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52322927', '52322926', 'Buch']),
        list(['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52323198', '52323197', 'Buch'])],
       dtype=object),
 'dateistrings': ['Das ist ein neues\nHaus Maus Buch',
  'Was kostet das neue Buch?\nBuch Haus Maus'],
 'df4': <generator object RePatterns._generator_json.<locals>.<genexpr> at 0x0000000012D56820>,
 'df5': array([list(['<stdin>', '1', '9', '8', 'mein']),
        list(['<stdin>', '1', '14', '13', 'Buch']),
        list(['<stdin>', '1', '35', '34', 'Buch'])], dtype=object),
 'df6': array([list(['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '515', '514', 'Auto']),
        list(['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '543', '542', 'Auto']),
        list(['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '3358', '3357', 'Auto']),
        ...,
        list(['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '52423818', '52423817', 'Auto']),
        list(['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '52426297', '52426296', 'Auto']),
        list(['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '52426444', '52426443', 'Auto'])],
       dtype=object),
 'df7': <generator object RePatterns._generator_json.<locals>.<genexpr> at 0x0000000012B8C9E0>,
 'df8': <generator object RePatterns._generator_json.<locals>.<genexpr> at 0x0000000013209F20>,

 'df9': array([list(['F:\\nur_df\\wiki0001.txt', '1', '330', '329', '1968 infol']),
        list(['F:\\nur_df\\wiki0001.txt', '1', '1916', '1915', '2007 sende']),
        list(['F:\\nur_df\\wiki0001.txt', '1', '3079', '3078', '2000 immer']),
        ...,
        list(['F:\\nur_df\\wiki0001.txt', '1', '2016132', '2016131', '75 Jahre']),
        list(['F:\\nur_df\\wiki0001.txt', '1', '2016203', '2016202', '2005 emeri']),
        list(['F:\\nur_df\\wiki0001.txt', '1', '2017110', '2017109', '85 Jahre'])],
       dtype=object),
 'df10': array([list(['F:\\nur_df', '1', '205', '204', '30 Kilom']),
        list(['F:\\nur_df', '1', '245', '244', '30 Kilom']),
        list(['F:\\nur_df', '1', '292', '291', '60 Kilom']), ...,
        list(['F:\\nur_df', '1', '2016132', '2016131', '75 Jahre']),
        list(['F:\\nur_df', '1', '2016203', '2016202', '2005 emeri']),
        list(['F:\\nur_df', '1', '2017110', '2017109', '85 Jahre'])],
       dtype=object),
 'df11': array([list(['F:\\nur_df', '1', '205', '204', 'Kilom']),
        list(['F:\\nur_df', '1', '242', '241', 'Kilom']),
        list(['F:\\nur_df', '1', '286', '285', 'Kilom']), ...,
        list(['F:\\nur_df', '1', '2006047', '2006046', 'Jahre']),
        list(['F:\\nur_df', '1', '2006115', '2006114', 'emeri']),
        list(['F:\\nur_df', '1', '2007017', '2007016', 'Jahre'])],
       dtype=object),
 'df12': array([list(['<stdin>', '1', '21', '20', '6. Janua']),
        list(['<stdin>', '1', '303', '302', '18 Jahre']),
        list(['<stdin>', '1', '555', '554', '6. Janua']),
        list(['<stdin>', '1', '803', '802', '6. Janua'])], dtype=object),
 'df13': array([list(['<stdin>', '1', '21', '20', 'dudu Janua']),
        list(['<stdin>', '1', '305', '304', 'dudu Jahre']),
        list(['<stdin>', '1', '559', '558', 'dudu Janua']),
        list(['<stdin>', '1', '809', '808', 'dudu Janua'])], dtype=object),
 'df14': <generator object RePatterns._generator_json.<locals>.<genexpr> at 0x000000001A28A120>,
 'dfxx':                             aa_filename  aa_line  ...  aa_byte_offset_o  aa_string
 0        F:\woerterbuecher\wtxt\xaa.txt        1  ...                 5        ter
 1        F:\woerterbuecher\wtxt\xaa.txt        1  ...                32        ber
 2        F:\woerterbuecher\wtxt\xaa.txt        1  ...                51        ton
 3        F:\woerterbuecher\wtxt\xaa.txt        1  ...                73        ber
 4        F:\woerterbuecher\wtxt\xaa.txt        1  ...               132        der
 ...                                 ...      ...  ...               ...        ...
 3280734  F:\woerterbuecher\wtxt\xaa.txt        1  ...          52428724        ter
 3280735  F:\woerterbuecher\wtxt\xaa.txt        1  ...          52428741        der
 3280736  F:\woerterbuecher\wtxt\xaa.txt        1  ...          52428753        eyr
 3280737  F:\woerterbuecher\wtxt\xaa.txt        1  ...          52428770        ler
 3280738  F:\woerterbuecher\wtxt\xaa.txt        1  ...          52428797        ine
 
 [3280739 rows x 5 columns],

```


This is how you can use the class PyRipGREP directly (output as string!):
```python
        dfa_size: str = "1G",
        regexstart = PyRipGREP()
        search_for = _to_list(re_expression)
        for suche in search_for:
            regexstart.regexp(option=suche, activated=True, multi_allowed=True)

        (
            regexstart
            .binary(activated=True)
            .byte_offset(activated=True) 
            .context_separator(option=" ")
            .dfa_size_limit(option=dfa_size)
            .field_match_separator(option= "ÇÇ") 
            .ignore_case(activated=True)
            .null_data(activated=True)
            .line_number(activated=True)
            .no_ignore(activated=True)
            .multiline(activated=True)
            .multiline_dotall(activated=True)
            .block_buffered(activated=True)
            .crlf(activated=True)
            .no_config(activated=True)
            .only_matching(activated=True)
            .trim(activated=True)
            .vimgrep(activated=True)
            .with_filename(activated=True)
            .add_target_file_or_folder('c:\\whatever.txt')
        )

```
