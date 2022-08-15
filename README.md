# PYRipGREP
Use the insanely fast regex engine RIPGREP https://github.com/BurntSushi/ripgrep as a python module! Search results are converted directly to dict/numpy/pandas/generator

You can use the class PyRipGREP as you would use ripgrep, but you will get a string as result. Because of that I created the class RePatterns where your results are converted in a format that allows you to work with big datasets! 

Check it out:
You'll find the files xaa.txt / xab.txt here: https://github.com/hansalemaos/PYRipGREP/tree/main/textfilesfortests



```
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
