# PYRipGREP

Use the insanely fast regex engine RIPGREP https://github.com/BurntSushi/ripgrep as a python module! Search results are converted directly to dict/numpy/pandas/generator

You can use the class ```PyRipGREP``` as you would use ripgrep, but you will get a string as result. Because of that, I created the class ```RePatterns ``` where your results are directly converted to dict/numpy/pandas/generator

```python
#Install
pip install PyRipGrep
```

Check it out:
You'll find the files xaa.txt / xab.txt here: https://github.com/hansalemaos/PYRipGREP/tree/main/textfilesfortests
Make sure to have rg.exe in your path or pass the path when you create the instance: 

```python
from PyRipGrep import RePatterns
RePatterns(executeable=r"c:\path\rg.exe")
```

```python
    outputtype = "np"
    suchennach = ["weniger", "mehr"]
    filetosearch = [
        r"F:\woerterbuecher\wtxt\xaa.txt", # download here: https://github.com/hansalemaos/PYRipGREP/blob/main/textfilesfortests/xaa.txt
        r"F:\woerterbuecher\wtxt\xab.txt", #download here: https://github.com/hansalemaos/PYRipGREP/blob/main/textfilesfortests/xab.txt
    ]
    np_or_df = "np"
    binary = True
    dfa_size = "1G"  # Yes, I have a lot of RAM hahaha
    ignore_case = True
    df = RePatterns(executeable=r"rg.exe").find_all_in_files(
        re_expression=suchennach,
        path_to_search=filetosearch,
        outputtype=outputtype,
        binary=binary,
        dfa_size=dfa_size,
        ignore_case=ignore_case,
    )
    print(f"{df=}")

    
#########################################################    
    
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
    
#########################################################    
   
    df3 = RePatterns().find_all_in_files(
        re_expression=[r"Buch"],
        path_to_search=filetosearch,
        outputtype=outputtype,
        binary=False,
        dfa_size=dfa_size,
        ignore_case=ignore_case,
    )
    print(f"{df3=}")

#########################################################    
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
#########################################################    
    df5 = RePatterns().find_all_in_var(
        re_expression=["mein", r"Buch"],
        variable="Das ist mein Buch. Wo hast du das Buch gekauft?",
        outputtype=outputtype,
        binary=False,
        dfa_size=dfa_size,
        ignore_case=ignore_case,
    )
    print(f"{df5=}")
#########################################################    
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
#########################################################    
    df7 = RePatterns().find_all_in_files_json(
        re_expression=[r"Buch", "Haus"],
        search_in=filetosearch,
        outputtype=outputtype,
        binary=True,
        ignore_case=True,
    )
    print(f"{df7=}")
#########################################################    
    df8 = RePatterns().find_all_in_files_json(
        re_expression=[r"Buch", "Haus"],
        search_in=r"F:\nur_df",
        outputtype=outputtype,
        binary=True,
        ignore_case=True,
    )
    print(f"{df8=}")
#########################################################    
    text = r"""Guy Reffitt, der am 6. Januar am Sturm aufs US-Kapitol teilnahm, muss f??r sieben Jahre ins Gef??ngnis. Der stern hat seine Familie anderthalb Jahre lang begleitet ??? bis zum Urteil gestern in Washington. ??ber einen Tag vor Gericht, der Amerikas ganze Verlorenheit offenbart.
    Am Ende ist es eine 18 Jahre junge Frau aus Texas, gerade mit der High School fertig, die den Satz des Tages sagt: "Wenn mein Vater so lange ins Gef??ngnis muss", sagt sie, "dann verdient Trump lebenslang."

    Es ist Peyton Reffitt, die Tochter eines Mannes, der am 6. Januar 2021 am Sturm aufs Kapitol teilnahm. Der stern hat die ganze Familie, die nicht mehr ganz ist, seitdem begleitet. Gestern wurde Peytons Vater, Guy Reffitt, in Washington zu ??ber sieben Jahren Haft verurteilt. Bei niemandem sonst, der am 6. Januar dabei war, fiel das Urteil bisher so hoch aus."""

    df9 = RePatterns().find_all_in_files(
        re_expression=r"\d+\s+\w{5}",
        path_to_search=filetosearch[0],
        outputtype=outputtype,
    )
    print(f"{df9=}")
    #########################################################    

    df10 = RePatterns().find_all_in_files(
        re_expression=r"\d+\s+\w{5}",
        path_to_search=r"F:\nur_df",
        outputtype=outputtype,
    )
    print(f"{df10=}")
    #########################################################    

    df11 = RePatterns().sub_in_files(
        re_expression=r"\d+\s+(\w{5})",
        repl="$1",
        path_to_search=r"F:\nur_df",
        outputtype=outputtype,
    )
    print(f"{df11=}")
    #########################################################    

    df12 = RePatterns().find_all_in_var(
        re_expression=r"\d+\.?\s+\w{5}", variable=text, outputtype=outputtype
    )
    print(f"{df12=}")
    #########################################################    

    df13 = RePatterns().sub_all_in_var(
        re_expression=r"\d+\.?\s+(\w{5})",
        repl="dudu $1",
        variable=text,
        outputtype=outputtype,
    )
    print(f"{df13=}")
    #########################################################    

    df14 = RePatterns().find_all_in_var_json(
        re_expression=r"\d+\.?\s+(\w{5})[.?!]", variable=text, outputtype=outputtype
    )
    print(f"{df14=}")
    #########################################################    

    suchennach = ["Sein"]

    dfxx = RePatterns().find_all_in_files(
        re_expression=r"\w\w[ener]\b",
        path_to_search=filetosearch[1],
        outputtype="df",
        binary=True,
        dfa_size="1G",
        ignore_case=True,
    )
    print(f"{dfxx=}")
```

Output: 

```python
    df=array([['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '15243', '15242',
        'Mehr'],
       ['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '22162', '22161',
        'mehr'],
       ['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '26981', '26980',
        'mehr'],
       ...,
       ['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52397917', '52397916',
        'mehr'],
       ['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52403287', '52403286',
        'mehr'],
       ['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52404523', '52404522',
        'mehr']], dtype='<U30')
df2=array([['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '4966', '4965', 'sein'],
       ['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '5021', '5020', 'sein'],
       ['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '7164', '7163', 'Sein'],
       ...,
       ['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52415836', '52415835',
        'sein'],
       ['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52420887', '52420886',
        'sein'],
       ['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52422346', '52422345',
        'Sein']], dtype='<U30')
df3=array([['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '1051', '1050', 'buch'],
       ['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '28055', '28054',
        'buch'],
       ['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '31815', '31814',
        'Buch'],
       ...,
       ['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52302767', '52302766',
        'buch'],
       ['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52322927', '52322926',
        'Buch'],
       ['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52323198', '52323197',
        'Buch']], dtype='<U30')
df4=<generator object RePatterns._generator_json.<locals>.<genexpr> at 0x00000000129C8820>
df5=array([['<stdin>', '1', '9', '8', 'mein'],
       ['<stdin>', '1', '14', '13', 'Buch'],
       ['<stdin>', '1', '35', '34', 'Buch']], dtype='<U7')
df6=array([['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '515', '514', 'Auto'],
       ['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '543', '542', 'Auto'],
       ['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '3358', '3357', 'Auto'],
       ...,
       ['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '52423818', '52423817',
        'Auto'],
       ['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '52426297', '52426296',
        'Auto'],
       ['F:\\woerterbuecher\\wtxt\\xab.txt', '1', '52426444', '52426443',
        'Auto']], dtype='<U30')
df7=<generator object RePatterns._generator_json.<locals>.<genexpr> at 0x00000000129B4DD0>
df8=<generator object RePatterns._generator_json.<locals>.<genexpr> at 0x00000000129E8890>
df9=array([['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '493', '492',
        '1904 verfa'],
       ['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '840', '839',
        '1925 ??bern'],
       ['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '890', '889',
        '1935 schuf'],
       ...,
       ['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52428295', '52428294',
        '2001 B??rge'],
       ['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52428359', '52428358',
        '1991 B??rge'],
       ['F:\\woerterbuecher\\wtxt\\xaa.txt', '1', '52428418', '52428417',
        '1979 B??rge']], dtype='<U30')
df10=array([['F:\\nur_df', '1', '205', '204', '30 Kilom'],
       ['F:\\nur_df', '1', '245', '244', '30 Kilom'],
       ['F:\\nur_df', '1', '292', '291', '60 Kilom'],
       ...,
       ['F:\\nur_df', '1', '2016132', '2016131', '75 Jahre'],
       ['F:\\nur_df', '1', '2016203', '2016202', '2005 emeri'],
       ['F:\\nur_df', '1', '2017110', '2017109', '85 Jahre']],
      dtype='<U14')
df11=array([['F:\\nur_df', '1', '205', '204', 'Kilom'],
       ['F:\\nur_df', '1', '242', '241', 'Kilom'],
       ['F:\\nur_df', '1', '286', '285', 'Kilom'],
       ...,
       ['F:\\nur_df', '1', '2111612', '2111611', 'Carlo'],
       ['F:\\nur_df', '1', '2111911', '2111910', 'gelan'],
       ['F:\\nur_df', '1', '2113124', '2113123', 'verf??']], dtype='<U9')
df12=array([['<stdin>', '1', '21', '20', '6. Janua'],
       ['<stdin>', '1', '303', '302', '18 Jahre'],
       ['<stdin>', '1', '551', '550', '6. Janua'],
       ['<stdin>', '1', '799', '798', '6. Janua']], dtype='<U8')
df13=array([['<stdin>', '1', '21', '20', 'dudu Janua'],
       ['<stdin>', '1', '305', '304', 'dudu Jahre'],
       ['<stdin>', '1', '555', '554', 'dudu Janua'],
       ['<stdin>', '1', '805', '804', 'dudu Janua']], dtype='<U10')
df14=<generator object RePatterns._generator_json.<locals>.<genexpr> at 0x00000000129E8E40>
dfxx=                            aa_filename  aa_line  ...  aa_byte_offset_o  aa_string
0        F:\woerterbuecher\wtxt\xab.txt        1  ...                10        von
1        F:\woerterbuecher\wtxt\xab.txt        1  ...                33        tin
2        F:\woerterbuecher\wtxt\xab.txt        1  ...                46        ber
3        F:\woerterbuecher\wtxt\xab.txt        1  ...                78        ber
4        F:\woerterbuecher\wtxt\xab.txt        1  ...                85        ton
                                 ...      ...  ...               ...        ...
3035300  F:\woerterbuecher\wtxt\xab.txt        1  ...          52428744        che
3035301  F:\woerterbuecher\wtxt\xab.txt        1  ...          52428756        che
3035302  F:\woerterbuecher\wtxt\xab.txt        1  ...          52428775        rde
3035303  F:\woerterbuecher\wtxt\xab.txt        1  ...          52428782        der
3035304  F:\woerterbuecher\wtxt\xab.txt        1  ...          52428790        ten
[3035305 rows x 5 columns]
```

### This is how you can use the class PyRipGREP directly (output as string!):

```python
        from PyRipGrep import PyRipGREP
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
            .field_match_separator(option= "????") 
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
