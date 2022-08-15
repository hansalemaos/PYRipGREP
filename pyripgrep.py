import subprocess
from typing import Union
import pandas as pd
import re
import regex
import ujson  # python -m pip install ujson
from dfprinter import PandasPrinter
import numpy as np
from tempfile import SpooledTemporaryFile as tempfile

d = lambda x: PandasPrinter(x, column_max_width=200).print_pd()


class Trie:
    """
    Tr = Trie()
    Tr.trie_regex_from_words(['ich', 'du', 'er', 'sie', 'es', 'wir', 'der', 'die', 'das'])
    text = '''Der zur Verlagsgruppe Holtzbrinck gehörende Verlag S. Fischer hat bzw. hatte die Nutzungsrechte an Werken von Autoren wie Thomas und Heinrich Mann. Das Urheberrecht läuft in Deutschland erst 70 Jahre nach dem Tod des Autors aus. In den USA sind diese Werke aber schon vorher gemeinfrei (public domain), hier 56 Jahre nach Veröffentlichung.
    Der Verlag ließ sich von der für Massenabmahnungen berüchtigten Kanzlei Waldorf Frommer vertreten.[7] Er forderte die Entfernung von 18 Werken, außerdem Schadenersatz und die Offenlegung aller IP-Adressen, von denen aus jene Werke heruntergeladen worden waren.
    Das Landgericht Frankfurt am Main urteilte, dass die Werke in Deutschland unzugänglich gemacht werden dürfen, aber nicht entfernt werden müssen.[8] Die Serverlogs waren schon gelöscht, weshalb keine IPs herausgegeben werden konnten.
    Als Folge des Urteils wurde das gesamte Angebot von Project Gutenberg für deutsche IP-Adressen gesperrt.
    Der Verlag kritisierte die Praxis des Project Gutenberg, weil damit auch die übergroße Mehrzahl gemeinfreier Texte nicht mehr frei abrufbar sei, was nicht das Ziel der Klage gewesen sei. Dies lege „aus Sicht des Verlags doch den Schluss nahe, dass man die Nutzer instrumentalisieren und zu Protesten gegen den Verlag veranlassen will“.[9][10] Das Project Gutenberg sah sich andererseits der Gefahr ausgesetzt, auch wegen weiterer Titel mit derselben Problematik verklagt zu werden.[5]
    Der 11. Zivilsenat des Oberlandesgerichts Frankfurt am Main (OLG) bestätigte mit Urteil vom 30. April 2019 – Az. 11 O 27/18 – die Entscheidung des Landgerichts.[11] Die Revision ließ das Oberlandesgericht Frankfurt nicht zu.[12] Gegen das Urteil des OLG Frankfurt war nur die Möglichkeit der Nichtzulassungsbeschwerde beim Bundesgerichtshof gegeben (Az. I ZR 97/19).[13]
    Im Oktober 2021 wurde die Beilegung des Rechtsstreits bekannt gegeben. Die generelle Blockade deutscher IP-Adressen wurde aufgehoben, gesperrt sind lediglich noch die Werke der drei im Rechtsstreit benannten Autoren, soweit deren Urheberrecht in Deutschland noch nicht ausgelaufen ist.[4]'''
    result = Tr.find(text)
    print(result)
    """

    def __init__(self):
        self.data = {}
        self.union = ""

    def add(self, word):
        ref = self.data
        for char in word:
            ref[char] = char in ref and ref[char] or {}
            ref = ref[char]
        ref[""] = 1

    def dump(self):
        return self.data

    def quote(self, char):
        return re.escape(char)

    def _pattern(self, pData):
        data = pData
        if "" in data and len(data.keys()) == 1:
            return None

        alt = []
        cc = []
        q = 0
        for char in sorted(data.keys()):
            if isinstance(data[char], dict):
                try:
                    recurse = self._pattern(data[char])
                    alt.append(self.quote(char) + recurse)
                except:
                    cc.append(self.quote(char))
            else:
                q = 1
        cconly = not len(alt) > 0

        if len(cc) > 0:
            if len(cc) == 1:
                alt.append(cc[0])
            else:
                alt.append("[" + "".join(cc) + "]")

        if len(alt) == 1:
            result = alt[0]
        else:
            result = "(?:" + "|".join(alt) + ")"

        if q:
            if cconly:
                result += "?"
            else:
                result = "(?:%s)?" % result
        return result

    def pattern(self):
        return self._pattern(self.dump())

    def trie_regex_from_words(
        self,
        words,
        boundary_right=True,
        boundary_left=True,
        capture=False,
        ignorecase=False,
        match_whole_line=False,
    ):
        for word in words:
            self.add(word)
        anfang = ""
        ende = ""
        if match_whole_line is True:
            anfang = anfang + r"^\s*"
        if boundary_right is True:
            ende = ende + r"\b"
        if capture is True:
            anfang = anfang + "("
        if boundary_left is True:
            anfang = anfang + r"\b"
        if capture is True:
            ende = ende + ")"

        if match_whole_line is True:
            ende = ende + r"\s*$"
        if ignorecase is True:
            self.union = regex.compile(anfang + self.pattern() + ende, regex.IGNORECASE)
        else:
            self.union = regex.compile(anfang + self.pattern() + ende)


class PDTools:
    def __init__(self, dataframe):
        self.dataframe = dataframe

    def bb_return_copy(self):
        return self.dataframe.copy()

    def aa_pd_horizonal_explode(
        self,
        what_columns: iter,
        zfill: int = 4,
        handle_nan: bool = True,
        delete_old_cols: bool = True,
    ):
        dataframe = self.bb_return_copy()
        for col in what_columns:
            if handle_nan:
                pattern = dataframe[dataframe[col].isna()].index
                if not pattern.empty:
                    howmanyelements = len(
                        dataframe.loc[~dataframe.index.isin(pattern), col].iloc[0]
                    )
                    dataframe.loc[pattern, col] = [[None] * howmanyelements] * len(
                        pattern
                    )
            spittedlists = np.fromiter(
                (
                    np.fromiter(_, dataframe[col].dtype)
                    for _ in zip(*dataframe[col].__array__())
                ),
                dataframe[col].dtype,
            )
            for ini, splittedlist in enumerate(spittedlists):
                dataframe[f"{col}_{str(ini).zfill(zfill)}"] = splittedlist
        if delete_old_cols:
            return dataframe.drop(columns=what_columns)
        self.dataframe = dataframe.copy()
        return self


class PyRipGREP:
    def __init__(
        self,
        executeable=r"C:\Users\Gamer\scoop\apps\ripgrep\current\rg.exe",
        option_targetfile=None,
    ):

        self.tempfile_for_vars = "PyRipGREP.PyRtmp"
        self.delete_tempfile_for_vars_search = False
        self.executeable = executeable
        self.necessary_beginning = [self.executeable]
        self.options_parameters = {
            "after_context": "--after-context",
            "auto_hybrid_regex": "--auto-hybrid-regex",
            "before_context": "--before-context",
            "binary": "--binary",
            "block_buffered": "--block-buffered",
            "byte_offset": "--byte-offset",
            "case_sensitive": "--case-sensitive",
            "color": "--color",
            "colors": "--colors",
            "column": "--column",
            "context": "--context",
            "context_separator": "--context-separator",
            "count": "--count",
            "count_matches": "--count-matches",
            "crlf": "--crlf",
            "debug": "--debug",
            "dfa_size_limit": "--dfa-size-limit",
            "encoding": "--encoding",
            "engine": "--engine",
            "field_context_separator": "--field-context-separator",
            "field_match_separator": "--field-match-separator",
            "file": "--file",
            "files": "--files",
            "files_with_matches": "--files-with-matches",
            "files_without_match": "--files-without-match",
            "fixed_strings": "--fixed-strings",
            "follow": "--follow",
            "glob": "--glob",
            "glob_case_insensitive": "--glob-case-insensitive",
            "help": "--help",
            "heading": "--heading",
            "hidden": "--hidden",
            "iglob": "--iglob",
            "ignore_case": "--ignore-case",
            "ignore_file": "--ignore-file",
            "ignore_file_case_insensitive": "--ignore-file-case-insensitive",
            "include_zero": "--include-zero",
            "invert_match": "--invert-match",
            "json": "--json",
            "line_buffered": "--line-buffered",
            "line_number": "--line-number",
            "line_regexp": "--line-regexp",
            "max_columns": "--max-columns",
            "max_columns_preview": "--max-columns-preview",
            "max_count": "--max-count",
            "max_depth": "--max-depth",
            "max_filesize": "--max-filesize",
            "mmap": "--mmap",
            "multiline": "--multiline",
            "multiline_dotall": "--multiline-dotall",
            "no_config": "--no-config",
            "no_filename": "--no-filename",
            "no_heading": "--no-heading",
            "no_ignore": "--no-ignore",
            "no_ignore_dot": "--no-ignore-dot",
            "no_ignore_exclude": "--no-ignore-exclude",
            "no_ignore_files": "--no-ignore-files",
            "no_ignore_global": "--no-ignore-global",
            "no_ignore_messages": "--no-ignore-messages",
            "no_ignore_parent": "--no-ignore-parent",
            "no_ignore_vcs": "--no-ignore-vcs",
            "no_line_number": "--no-line-number",
            "no_messages": "--no-messages",
            "no_mmap": "--no-mmap",
            "no_pcre2_unicode": "--no-pcre2-unicode",
            "no_require_git": "--no-require-git",
            "no_unicode": "--no-unicode",
            "null": "--null",
            "null_data": "--null-data",
            "one_file_system": "--one-file-system",
            "only_matching": "--only-matching",
            "passthru": "--passthru",
            "path_separator": "--path-separator",
            "pcre2": "--pcre2",
            "pcre2_version": "--pcre2-version",
            "pre": "--pre",
            "pretty": "--pretty",
            "quiet": "--quiet",
            "regex_size_limit": "--regex-size-limit",
            "regexp": "--regexp",
            "replace": "--replace",
            "search_zip": "--search-zip",
            "smart_case": "--smart-case",
            "sort": "--sort",
            "sortr": "--sortr",
            "stats": "--stats",
            "text": "--text",
            "threads": "--threads",
            "trim": "--trim",
            "type": "--type",
            "type_add": "--type-add",
            "type_clear": "--type-clear",
            "type_list": "--type-list",
            "type_not": "--type-not",
            "unrestricted": "--unrestricted",
            "version": "--version",
            "vimgrep": "--vimgrep",
            "with_filename": "--with-filename",
            "word_regexp": "--word-regexp",
        }
        self.execute_dict = {
            "--after-context": False,
            "--auto-hybrid-regex": False,
            "--before-context": False,
            "--binary": False,
            "--block-buffered": False,
            "--byte-offset": False,
            "--case-sensitive": False,
            "--color": False,
            "--colors": False,
            "--column": False,
            "--context": False,
            "--context-separator": False,
            "--count": False,
            "--count-matches": False,
            "--crlf": False,
            "--debug": False,
            "--dfa-size-limit": False,
            "--encoding": False,
            "--engine": False,
            "--field-context-separator": False,
            "--field-match-separator": False,
            "--file": False,
            "--files": False,
            "--files-with-matches": False,
            "--files-without-match": False,
            "--fixed-strings": False,
            "--follow": False,
            "--glob": False,
            "--glob-case-insensitive": False,
            "--help": False,
            "--heading": False,
            "--hidden": False,
            "--iglob": False,
            "--ignore-case": False,
            "--ignore-file": False,
            "--ignore-file-case-insensitive": False,
            "--include-zero": False,
            "--invert-match": False,
            "--json": False,
            "--line-buffered": False,
            "--line-number": False,
            "--line-regexp": False,
            "--max-columns": False,
            "--max-columns-preview": False,
            "--max-count": False,
            "--max-depth": False,
            "--max-filesize": False,
            "--mmap": False,
            "--multiline": False,
            "--multiline-dotall": False,
            "--no-config": False,
            "--no-filename": False,
            "--no-heading": False,
            "--no-ignore": False,
            "--no-ignore-dot": False,
            "--no-ignore-exclude": False,
            "--no-ignore-files": False,
            "--no-ignore-global": False,
            "--no-ignore-messages": False,
            "--no-ignore-parent": False,
            "--no-ignore-vcs": False,
            "--no-line-number": False,
            "--no-messages": False,
            "--no-mmap": False,
            "--no-pcre2-unicode": False,
            "--no-require-git": False,
            "--no-unicode": False,
            "--null": False,
            "--null-data": False,
            "--one-file-system": False,
            "--only-matching": False,
            "--passthru": False,
            "--path-separator": False,
            "--pcre2": False,
            "--pcre2-version": False,
            "--pre": False,
            "--pretty": False,
            "--quiet": False,
            "--regex-size-limit": False,
            "--regexp": False,
            "--replace": False,
            "--search-zip": False,
            "--smart-case": False,
            "--sort": False,
            "--sortr": False,
            "--stats": False,
            "--text": False,
            "--threads": False,
            "--trim": False,
            "--type": False,
            "--type-add": False,
            "--type-clear": False,
            "--type-list": False,
            "--type-not": False,
            "--unrestricted": False,
            "--version": False,
            "--vimgrep": False,
            "--with-filename": False,
            "--word-regexp": False,
        }
        self.helpdict = {
            "after_context": " Show NUM lines after each match.  This overrides the --context and --passthru flags.",
            "auto_hybrid_regex": " DEPRECATED. Use --engine instead.  When this flag is used, ripgrep will dynamically choose between\nsupported regex engines depending on the features used in a pattern. When ripgrep chooses a regex\nengine, it applies that choice for every regex provided to ripgrep (e.g., via multiple -e/--regexp\nor -f/--file flags).  As an example of how this flag might behave, ripgrep will attempt to use its\ndefault finite automata based regex engine whenever the pattern can be successfully compiled with\nthat regex engine. If PCRE2 is enabled and if the pattern given could not be compiled with the\ndefault regex engine, then PCRE2 will be automatically used for searching. If PCRE2 isn't available,\nthen this flag has no effect because there is only one regex engine to choose from.  In the future,\nripgrep may adjust its heuristics for how it decides which regex engine to use. In general, the\nheuristics will be limited to a static analysis of the patterns, and not to any specific runtime\nbehavior observed while searching files.  The primary downside of using this flag is that it may not\nalways be obvious which regex engine ripgrep uses, and thus, the match semantics or performance\nprofile of ripgrep may subtly and unexpectedly change. However, in many cases, all regex engines\nwill agree on what constitutes a match and it can be nice to transparently support more advanced\nregex features like look-around and backreferences without explicitly needing to enable them.  This\nflag can be disabled with --no-auto-hybrid-regex.",
            "before_context": " Show NUM lines before each match.  This overrides the --context and --passthru flags.",
            "binary": " Enabling this flag will cause ripgrep to search binary files. By default, ripgrep attempts to\nautomatically skip binary files in order to improve the relevance of results and make the search\nfaster.  Binary files are heuristically detected based on whether they contain a NUL byte or not. By\ndefault (without this flag set), once a NUL byte is seen, ripgrep will stop searching the file.\nUsually, NUL bytes occur in the beginning of most binary files. If a NUL byte occurs after a match,\nthen ripgrep will still stop searching the rest of the file, but a warning will be printed.  In\ncontrast, when this flag is provided, ripgrep will continue searching a file even if a NUL byte is\nfound. In particular, if a NUL byte is found then ripgrep will continue searching until either a\nmatch is found or the end of the file is reached, whichever comes sooner. If a match is found, then\nripgrep will stop and print a warning saying that the search stopped prematurely.  If you want\nripgrep to search a file without any special NUL byte handling at all (and potentially print binary\ndata to stdout), then you should use the '-a/--text' flag.  The '--binary' flag is a flag for\ncontrolling ripgrep's automatic filtering mechanism. As such, it does not need to be used when\nsearching a file explicitly or when searching stdin. That is, it is only applicable when recursively\nsearching a directory.  Note that when the '-u/--unrestricted' flag is provided for a third time,\nthen this flag is automatically enabled.  This flag can be disabled with '--no-binary'. It overrides\nthe '-a/--text' flag.",
            "block_buffered": " When enabled, ripgrep will use block buffering. That is, whenever a matching line is found, it will\nbe written to an in-memory buffer and will not be written to stdout until the buffer reaches a\ncertain size. This is the default when ripgrep's stdout is redirected to a pipeline or a file. When\nripgrep's stdout is connected to a terminal, line buffering will be used. Forcing block buffering\ncan be useful when dumping a large amount of contents to a terminal.  Forceful block buffering can\nbe disabled with --no-block-buffered. Note that using --no-block-buffered causes ripgrep to revert\nto its default behavior of automatically detecting the buffering strategy. To force line buffering,\nuse the --line-buffered flag.",
            "byte_offset": " Print the 0-based byte offset within the input file before each line of output. If -o (--only-\nmatching) is specified, print the offset of the matching part itself.  If ripgrep does transcoding,\nthen the byte offset is in terms of the the result of transcoding and not the original data. This\napplies similarly to another transformation on the source, such as decompression or a --pre filter.\nNote that when the PCRE2 regex engine is used, then UTF-8 transcoding is done by default.",
            "case_sensitive": " Search case sensitively.  This overrides the -i/--ignore-case and -S/--smart-case flags.",
            "color": " This flag controls when to use colors. The default setting is 'auto', which means ripgrep will try\nto guess when to use colors. For example, if ripgrep is printing to a terminal, then it will use\ncolors, but if it is redirected to a file or a pipe, then it will suppress color output. ripgrep\nwill suppress color output in some other circumstances as well. For example, if the TERM environment\nsearch_in is not set or set to 'dumb', then ripgrep will not use colors.  The possible values for\nthis flag are:  never    Colors will never be used. auto     The default. ripgrep tries to be smart.\nalways   Colors will always be used regardless of where output is sent. ansi     Like 'always', but\nemits ANSI escapes (even in a Windows console).  When the --vimgrep flag is given to ripgrep, then\nthe default value for the color flag changes to 'never'.",
            "colors": " This flag specifies color settings for use in the output. This flag may be provided multiple times.\nSettings are applied iteratively. Colors are limited to one of eight choices: red, blue, green,\ncyan, magenta, yellow, white and black. Styles are limited to nobold, bold, nointense, intense,\nnounderline or underline.  The format of the flag is '{type}:{attribute}:{value}'. '{type}' should\nbe one of path, line, column or match. '{attribute}' can be fg, bg or style. '{value}' is either a\ncolor (for fg and bg) or a text style. A special format, '{type}:none', will clear all color\nsettings for '{type}'.  For example, the following command will change the match color to magenta\nand the background color for line numbers to yellow:  rg --colors 'match:fg:magenta' --colors\n'line:bg:yellow' foo.  Extended colors can be used for '{value}' when the terminal supports ANSI\ncolor sequences. These are specified as either 'x' (256-color) or 'x,x,x' (24-bit truecolor) where x\nis a number between 0 and 255 inclusive. x may be given as a normal decimal number or a hexadecimal\nnumber, which is prefixed by `0x`.  For example, the following command will change the match\nbackground color to that represented by the rgb value (0,128,255):  rg --colors 'match:bg:0,128,255'\nor, equivalently,  rg --colors 'match:bg:0x0,0x80,0xFF'  Note that the the intense and nointense\nstyle flags will have no effect when used alongside these extended color codes.",
            "column": " Show column numbers (1-based). This only shows the column numbers for the first match on each line.\nThis does not try to account for Unicode. One byte is equal to one column. This implies --line-\nnumber.  This flag can be disabled with --no-column.",
            "context": " Show NUM lines before and after each match. This is equivalent to providing both the -B/--before-\ncontext and -A/--after-context flags with the same value.  This overrides both the -B/--before-\ncontext and -A/--after-context flags, in addition to the --passthru flag.",
            "context_separator": " The string used to separate non-contiguous context lines in the output. This is only used when one\nof the context flags is used (-A, -B or -C). Escape sequences like \x7f or      may be used. The\ndefault value is --.  When the context separator is set to an empty string, then a line break is\nstill inserted. To completely disable context separators, use the no-context-separator flag.",
            "count": " This flag suppresses normal output and shows the number of lines that match the given patterns for\neach file searched. Each file containing a match has its path and count printed on each line. Note\nthat this reports the number of lines that match and not the total number of matches, unless\n-U/--multiline is enabled. In multiline mode, --count is equivalent to --count-matches.  If only one\nfile is given to ripgrep, then only the count is printed if there is a match. The --with-filename\nflag can be used to force printing the file path in this case. If you need a count to be printed\nregardless of whether there is a match, then use --include-zero.  This overrides the --count-matches\nflag. Note that when --count is combined with --only-matching, then ripgrep behaves as if --count-\nmatches was given.",
            "count_matches": " This flag suppresses normal output and shows the number of individual matches of the given patterns\nfor each file searched. Each file containing matches has its path and match count printed on each\nline. Note that this reports the total number of individual matches and not the number of lines that\nmatch.  If only one file is given to ripgrep, then only the count is printed if there is a match.\nThe --with-filename flag can be used to force printing the file path in this case.  This overrides\nthe --count flag. Note that when --count is combined with only-matching, then ripgrep behaves as if\n--count-matches was given.",
            "crlf": " When enabled, ripgrep will treat CRLF (') as a line terminator instead of just '.  Principally,\nthis permits '$' in regex patterns to match just before CRLF instead of just before LF. The\nunderlying regex engine may not support this natively, so ripgrep will translate all instances of\n'$' to '(?:??$)'. This may produce slightly different than desired match offsets. It is intended as\na work-around until the regex engine supports this natively.  CRLF support can be disabled with\n--no-crlf.",
            "debug": " Show debug messages. Please use this when filing a bug report.  The --debug flag is generally\nuseful for figuring out why ripgrep skipped searching a particular file. The debug messages should\nmention all files skipped and why they were skipped.  To get even more debug output, use the --trace\nflag, which implies --debug along with additional trace data. With --trace, the output could be\nquite large and is generally more useful for development.",
            "dfa_size_limit": " The upper size limit of the regex DFA. The default limit is 10M. This should only be changed on\nvery large regex inputs where the (slower) fallback regex engine may otherwise be used if the limit\nis reached.  The argument accepts the same size suffixes as allowed in with the max-filesize flag.",
            "encoding": " Specify the text encoding that ripgrep will use on all files searched. The default value is 'auto',\nwhich will cause ripgrep to do a best effort automatic detection of encoding on a per-file basis.\nAutomatic detection in this case only applies to files that begin with a UTF-8 or UTF-16 byte-order\nmark (BOM). No other automatic detection is performed. One can also specify 'none' which will then\ncompletely disable BOM sniffing and always result in searching the raw bytes, including a BOM if\nit's present, regardless of its encoding.  Other supported values can be found in the list of labels\nhere: https://encoding.spec.whatwg.org/#concept-encoding-get  For more details on encoding and how\nripgrep deals with it, see GUIDE.md.  This flag can be disabled with --no-encoding.",
            "engine": " Specify which regular expression engine to use. When you choose a regex engine, it applies that\nchoice for every regex provided to ripgrep (e.g., via multiple -e/--regexp or -f/--file flags).\nAccepted values are 'default', 'pcre2', or 'auto'.  The default value is 'default', which is the\nfastest and should be good for most use cases. The 'pcre2' engine is generally useful when you want\nto use features such as look-around or backreferences. 'auto' will dynamically choose between\nsupported regex engines depending on the features used in a pattern on a best effort basis.  Note\nthat the 'pcre2' engine is an optional ripgrep feature. If PCRE2 wasn't included in your build of\nripgrep, then using this flag will result in ripgrep printing an error message and exiting.  This\noverrides previous uses of --pcre2 and --auto-hybrid-regex flags. [default: default]",
            "field_context_separator": " Set the field context separator, which is used to delimit file paths, line numbers, columns and the\ncontext itself, when printing contextual lines. The separator may be any number of bytes, including\nzero. Escape sequences like \x7f or        may be used. The default value is -.",
            "field_match_separator": " Set the field match separator, which is used to delimit file paths, line numbers, columns and the\nmatch itself. The separator may be any number of bytes, including zero. Escape sequences like \x7f or\nmay be used. The default value is -.",
            "file": " Search for patterns from the given file, with one pattern per line. When this flag is used multiple\ntimes or in combination with the -e/--regexp flag, then all patterns provided are searched. Empty\npattern lines will match all input lines, and the newline is not counted as part of the pattern.  A\nline is printed if and only if it matches at least one of the patterns.",
            "files": " Print each file that would be searched without actually performing the search. This is useful to\ndetermine whether a particular file is being searched or not.",
            "files_with_matches": " Print the paths with at least one match and suppress match contents.  This overrides --files-\nwithout-match.",
            "files_without_match": " Print the paths that contain zero matches and suppress match contents. This inverts/negates the\n--files-with-matches flag.  This overrides --files-with-matches.",
            "fixed_strings": " Treat the pattern as a literal string instead of a regular expression. When this flag is used,\nspecial regular expression meta characters such as .(){}*+ do not need to be escaped.  This flag can\nbe disabled with --no-fixed-strings.",
            "follow": " When this flag is enabled, ripgrep will follow symbolic links while traversing directories. This is\ndisabled by default. Note that ripgrep will check for symbolic link loops and report errors if it\nfinds one.  This flag can be disabled with --no-follow.",
            "glob": " Include or exclude files and directories for searching that match the given glob. This always\noverrides any other ignore logic. Multiple glob flags may be used. Globbing rules match .gitignore\nglobs. Precede a glob with a ! to exclude it. If multiple globs match a file or directory, the glob\ngiven later in the command line takes precedence.  As an extension, globs support specifying\nalternatives: *-g ab{c,d}* is equivalet to *-g abc -g abd*. Empty alternatives like *-g ab{,c}* are\nnot currently supported. Note that this syntax extension is also currently enabled in gitignore\nfiles, even though this syntax isn't supported by git itself. ripgrep may disable this syntax\nextension in gitignore files, but it will always remain available via the -g/--glob flag.  When this\nflag is set, every file and directory is applied to it to test for a match. So for example, if you\nonly want to search in a particular directory 'foo', then *-g foo* is incorrect because 'foo/bar'\ndoes not match the glob 'foo'. Instead, you should use *-g 'foo/**'*.",
            "glob_case_insensitive": " Process glob patterns given with the -g/--glob flag case insensitively. This effectively treats\n--glob as --iglob.  This flag can be disabled with the --no-glob-case-insensitive flag.",
            "help": " Prints help information. Use --help for more details.",
            "heading": " This flag prints the file path above clusters of matches from each file instead of printing the\nfile path as a prefix for each matched line. This is the default mode when printing to a terminal.\nThis overrides the --no-heading flag.",
            "hidden": " Search hidden files and directories. By default, hidden files and directories are skipped. Note\nthat if a hidden file or a directory is whitelisted in an ignore file, then it will be searched even\nif this flag isn't provided.  A file or directory is considered hidden if its base name starts with\na dot character ('.'). On operating systems which support a `hidden` file attribute, like Windows,\nfiles with this attribute are also considered hidden.  This flag can be disabled with --no-hidden.",
            "iglob": " Include or exclude files and directories for searching that match the given glob. This always\noverrides any other ignore logic. Multiple glob flags may be used. Globbing rules match .gitignore\nglobs. Precede a glob with a ! to exclude it. Globs are matched case insensitively.",
            "ignore_case": ' When this flag is provided, the given patterns will be searched case insensitively. The case\ninsensitivity rules used by ripgrep conform to Unicode\'s "simple" case folding rules.  This flag\noverrides -s/--case-sensitive and -S/--smart-case.',
            "ignore_file": " Specifies a path to one or more .gitignore format rules files. These patterns are applied after the\npatterns found in .gitignore and .ignore are applied and are matched relative to the current working\ndirectory. Multiple additional ignore files can be specified by using the --ignore-file flag several\ntimes. When specifying multiple ignore files, earlier files have lower precedence than later files.\nIf you are looking for a way to include or exclude files and directories directly on the command\nline, then used -g instead.",
            "ignore_file_case_insensitive": " Process ignore files (.gitignore, .ignore, etc.) case insensitively. Note that this comes with a\nperformance penalty and is most useful on case insensitive file systems (such as Windows).  This\nflag can be disabled with the --no-ignore-file-case-insensitive flag.",
            "include_zero": " When used with --count or --count-matches, print the number of matches for each file even if there\nwere zero matches. This is disabled by default but can be enabled to make ripgrep behave more like\ngrep.",
            "invert_match": " Invert matching. Show lines that do not match the given patterns.",
            "json": " Enable printing results in a JSON Lines format.  When this flag is provided, ripgrep will emit a\nsequence of messages, each encoded as a JSON object, where there are five different message types:\n**begin** - A message that indicates a file is being searched and contains at least one match.\n**end** - A message the indicates a file is done being searched. This message also include summary\nstatistics about the search for a particular file.  **match** - A message that indicates a match was\nfound. This includes the text and offsets of the match.  **context** - A message that indicates a\ncontextual line was found. This includes the text of the line, along with any match information if\nthe search was inverted.  **summary** - The final message emitted by ripgrep that contains summary\nstatistics about the search across all files.  Since file paths or the contents of files are not\nguaranteed to be valid UTF-8 and JSON itself must be representable by a Unicode encoding, ripgrep\nwill emit all data elements as objects with one of two keys: 'text' or 'bytes'. 'text' is a normal\nJSON string when the data is valid UTF-8 while 'bytes' is the base64 encoded contents of the data.\nThe JSON Lines format is only supported for showing search results. It cannot be used with other\nflags that emit other types of output, such as --files, files-with-matches, --files-without-match,\n--count or --count-matches. ripgrep will report an error if any of the aforementioned flags are used\nin concert with --json.  Other flags that control aspects of the standard output such as only-\nmatching, --heading, --replace, --max-columns, etc., have no effect when --json is set.  A more\ncomplete description of the JSON format used can be found here: https://docs.rs/grep-\nprinter/*/grep_printer/struct.JSON.html  The JSON Lines format can be disabled with --no-json.",
            "line_buffered": " When enabled, ripgrep will use line buffering. That is, whenever a matching line is found, it will\nbe flushed to stdout immediately. This is the default when ripgrep's stdout is connected to a\nterminal, but otherwise, ripgrep will use block buffering, which is typically faster. This flag\nforces ripgrep to use line buffering even if it would otherwise use block buffering. This is\ntypically useful in shell pipelines, e.g., 'tail -f something.log | rg foo --line-buffered | rg\nbar'.  Forceful line buffering can be disabled with --no-line-buffered. Note that using --no-line-\nbuffered causes ripgrep to revert to its default behavior of automatically detecting the buffering\nstrategy. To force block buffering, use the --block-buffered flag.",
            "line_number": " Show line numbers (1-based). This is enabled by default when searching in a terminal.",
            "line_regexp": " Only show matches surrounded by line boundaries. This is equivalent to putting ^...$ around all of\nthe search patterns. In other words, this only prints lines where the entire line participates in a\nmatch.  This overrides the --word-regexp flag.",
            "max_columns": " Don't print lines longer than this limit in bytes. Longer lines are omitted, and only the number of\nmatches in that line is printed.  When this flag is omitted or is set to 0, then it has no effect.",
            "max_columns_preview": " When the '--max-columns' flag is used, ripgrep will by default completely replace any line that is\ntoo long with a message indicating that a matching line was removed. When this flag is combined with\n'--max-columns', a preview of the line (corresponding to the limit size) is shown instead, where the\npart of the line exceeding the limit is not shown.  If the '--max-columns' flag is not set, then\nthis has no effect.  This flag can be disabled with '--no-max-columns-preview'.",
            "max_count": " Limit the number of matching lines per file searched to NUM.",
            "max_depth": " Limit the depth of directory traversal to NUM levels beyond the paths given. A value of zero only\nsearches the explicitly given paths themselves.  For example, 'rg --max-depth 0 dir/' is a no-op\nbecause dir/ will not be descended into. 'rg --max-depth 1 dir/' will search only the direct\nchildren of 'dir'.",
            "max_filesize": " Ignore files larger than NUM in size. This does not apply to directories.  The input format accepts\nsuffixes of K, M or G which correspond to kilobytes, megabytes and gigabytes, respectively. If no\nsuffix is provided the input is treated as bytes.  Examples: --max-filesize 50K or --max-filesize\n80M",
            "mmap": " Search using memory maps when possible. This is enabled by default when ripgrep thinks it will be\nfaster.  Memory map searching doesn't currently support all options, so if an incompatible option\n(e.g., --context) is given with --mmap, then memory maps will not be used.  Note that ripgrep may\nabort unexpectedly when --mmap if it searches a file that is simultaneously truncated.  This flag\noverrides --no-mmap.",
            "multiline": " Enable matching across multiple lines.  When multiline mode is enabled, ripgrep will lift the\nrestriction that a match cannot include a line terminator. For example, when multiline mode is not\nenabled (the default), then the regex '\\p{any}' will match any Unicode codepoint other than '.\nSimilarly, the regex ' is explicitly forbidden, and if you try to use it, ripgrep will return an\nerror. However, when multiline mode is enabled, '\\p{any}' will match any Unicode codepoint,\nincluding ', and regexes like ' are permitted.  An important caveat is that multiline mode does\nnot change the match semantics of '.'. Namely, in most regex matchers, a '.' will by default match\nany character other than ', and this is true in ripgrep as well. In order to make '.' match ', you\nmust enable the \"dot all\" flag inside the regex. For example, both '(?s).' and '(?s:.)' have the\nsame semantics, where '.' will match any character, including '. Alternatively, the '--multiline-\ndotall' flag may be passed to make the \"dot all\" behavior the default. This flag only applies when\nmultiline search is enabled.  There is no limit on the number of the lines that a single match can\nspan.  **WARNING**: Because of how the underlying regex engine works, multiline searches may be\nslower than normal line-oriented searches, and they may also use more memory. In particular, when\nmultiline mode is enabled, ripgrep requires that each file it searches is laid out contiguously in\nmemory (either by reading it onto the heap or by memory-mapping it). Things that cannot be memory-\nmapped (such as stdin) will be consumed until EOF before searching can begin. In general, ripgrep\nwill only do these things when necessary. Specifically, if the --multiline flag is provided but the\nregex does not contain patterns that would match ' characters, then ripgrep will automatically\navoid reading each file into memory before searching it. Nevertheless, if you only care about\nmatches spanning at most one line, then it is always better to disable multiline mode.  This flag\ncan be disabled with --no-multiline.",
            "multiline_dotall": " This flag enables \"dot all\" in your regex pattern, which causes '.' to match newlines when\nmultiline searching is enabled. This flag has no effect if multiline searching isn't enabled with\nthe --multiline flag.  Normally, a '.' will match any character except newlines. While this behavior\ntypically isn't relevant for line-oriented matching (since matches can span at most one line), this\ncan be useful when searching with the -U/--multiline flag. By default, the multiline mode runs\nwithout this flag.  This flag is generally intended to be used in an alias or your ripgrep config\nfile if you prefer \"dot all\" semantics by default. Note that regardless of whether this flag is\nused, \"dot all\" semantics can still be controlled via inline flags in the regex pattern itself,\ne.g., '(?s:.)' always enables \"dot all\" whereas '(?-s:.)' always disables \"dot all\".  This flag can\nbe disabled with --no-multiline-dotall.",
            "no_config": " Never read configuration files. When this flag is present, ripgrep will not respect the\nRIPGREP_CONFIG_PATH environment search_in.  If ripgrep ever grows a feature to automatically read\nconfiguration files in pre-defined locations, then this flag will also disable that behavior as\nwell.",
            "no_filename": " Never print the file path with the matched lines. This is the default when ripgrep is explicitly\ninstructed to search one file or stdin.  This flag overrides --with-filename.",
            "no_heading": " Don't group matches by each file. If --no-heading is provided in addition to the -H/--with-filename\nflag, then file paths will be printed as a prefix for every matched line. This is the default mode\nwhen not printing to a terminal.  This overrides the --heading flag.",
            "no_ignore": " Don't respect ignore files (.gitignore, .ignore, etc.). This implies no-ignore-dot, --no-ignore-\nexclude, --no-ignore-global, no-ignore-parent and no-ignore-vcs.  This does *not* imply --no-ignore-\nfiles, since --ignore-file is specified explicitly as a command line argument.  When given only\nonce, the -u flag is identical in behavior to --no-ignore and can be considered an alias. However,\nsubsequent -u flags have additional effects; see --unrestricted.  This flag can be disabled with the\n--ignore flag.",
            "no_ignore_dot": " Don't respect .ignore files.  This does *not* affect whether ripgrep will ignore files and\ndirectories whose names begin with a dot. For that, see the -./--hidden flag.  This flag can be\ndisabled with the --ignore-dot flag.",
            "no_ignore_exclude": " Don't respect ignore files that are manually configured for the repository such as git's\n'.git/info/exclude'.  This flag can be disabled with the --ignore-exclude flag.",
            "no_ignore_files": " When set, any --ignore-file flags, even ones that come after this flag, are ignored.  This flag can\nbe disabled with the --ignore-files flag.",
            "no_ignore_global": " Don't respect ignore files that come from \"global\" sources such as git's `core.excludesFile`\nconfiguration option (which defaults to `$HOME/.config/git/ignore`).  This flag can be disabled with\nthe --ignore-global flag.",
            "no_ignore_messages": " Suppresses all error messages related to parsing ignore files such as .ignore or .gitignore.  This\nflag can be disabled with the --ignore-messages flag.",
            "no_ignore_parent": " Don't respect ignore files (.gitignore, .ignore, etc.) in parent directories.  This flag can be\ndisabled with the --ignore-parent flag.",
            "no_ignore_vcs": " Don't respect version control ignore files (.gitignore, etc.). This implies no-ignore-parent for\nVCS files. Note that .ignore files will continue to be respected.  This flag can be disabled with\nthe --ignore-vcs flag.",
            "no_line_number": " Suppress line numbers. This is enabled by default when not searching in a terminal.",
            "no_messages": " Suppress all error messages related to opening and reading files. Error messages related to the\nsyntax of the pattern given are still shown.  This flag can be disabled with the --messages flag.",
            "no_mmap": " Never use memory maps, even when they might be faster.  This flag overrides --mmap.",
            "no_pcre2_unicode": " DEPRECATED. Use --no-unicode instead.  This flag is now an alias for --no-unicode. And\n--pcre2-unicode is an alias for --unicode.",
            "no_require_git": " By default, ripgrep will only respect global gitignore rules, .gitignore rules and local exclude\nrules if ripgrep detects that you are searching inside a git repository. This flag allows you to\nrelax this restriction such that ripgrep will respect all git related ignore rules regardless of\nwhether you're searching in a git repository or not.  This flag can be disabled with --require-git.",
            "no_unicode": " By default, ripgrep will enable \"Unicode mode\" in all of its regexes. This has a number of\nconsequences:  * '.' will only match valid UTF-8 encoded scalar values. * Classes like '\\w', '\\s',\n'\\d' are all Unicode aware and much bigger than their ASCII only versions. * Case insensitive\nmatching will use Unicode case folding. * A large array of classes like '\\p{Emoji}' are available. *\nWord boundaries ('\x08' and '\\B') use the Unicode definition of a word character.  In some cases it can\nbe desirable to turn these things off. The --no-unicode flag will do exactly that.  For PCRE2\nspecifically, Unicode mode represents a critical trade off in the user experience of ripgrep. In\nparticular, unlike the default regex engine, PCRE2 does not support the ability to search possibly\ninvalid UTF-8 with Unicode features enabled. Instead, PCRE2 *requires* that everything it searches\nwhen Unicode mode is enabled is valid UTF-8. (Or valid UTF-16/UTF-32, but for the purposes of\nripgrep, we only discuss UTF-8.) This means that if you have PCRE2's Unicode mode enabled and you\nattempt to search invalid UTF-8, then the search for that file will halt and print an error. For\nthis reason, when PCRE2's Unicode mode is enabled, ripgrep will automatically \"fix\" invalid UTF-8\nsequences by replacing them with the Unicode replacement codepoint. This penalty does not occur when\nusing the default regex engine.  If you would rather see the encoding errors surfaced by PCRE2 when\nUnicode mode is enabled, then pass the --no-encoding flag to disable all transcoding.  The --no-\nunicode flag can be disabled with --unicode. Note that no-pcre2-unicode and --pcre2-unicode are\naliases for --no-unicode and unicode, respectively.",
            "null": " Whenever a file path is printed, follow it with a NUL byte. This includes printing file paths\nbefore matches, and when printing a list of matching files such as with --count, --files-with-\nmatches and --files. This option is useful for use with xargs.",
            "null_data": " Enabling this option causes ripgrep to use NUL as a line terminator instead of the default of '.\nThis is useful when searching large binary files that would otherwise have very long lines if '\nwere used as the line terminator. In particular, ripgrep requires that, at a minimum, each line must\nfit into memory. Using NUL instead can be a useful stopgap to keep memory requirements low and avoid\nOOM (out of memory) conditions.  This is also useful for processing NUL delimited data, such as that\nemitted when using ripgrep's -0/--null flag or find's --print0 flag.  Using this flag implies\n-a/--text.",
            "one_file_system": " When enabled, ripgrep will not cross file system boundaries relative to where the search started\nfrom.  Note that this applies to each path argument given to ripgrep. For example, in the command\n'rg --one-file-system /foo/bar /quux/baz', ripgrep will search both '/foo/bar' and '/quux/baz' even\nif they are on different file systems, but will not cross a file system boundary when traversing\neach path's directory tree.  This is similar to find's '-xdev' or '-mount' flag.  This flag can be\ndisabled with --no-one-file-system.",
            "only_matching": " Print only the matched (non-empty) parts of a matching line, with each such part on a separate\noutput line.",
            "passthru": " Print both matching and non-matching lines.  Another way to achieve a similar effect is by\nmodifying your pattern to match the empty string. For example, if you are searching using 'rg foo'\nthen using 'rg \"^|foo\"' instead will emit every line in every file searched, but only occurrences of\n'foo' will be highlighted. This flag enables the same behavior without needing to modify the\npattern.  This overrides the --context, --after-context and --before-context flags.",
            "path_separator": " Set the path separator to use when printing file paths. This defaults to your platform's path\nseparator, which is / on Unix and \\ on Windows. This flag is intended for overriding the default\nwhen the environment demands it (e.g., cygwin). A path separator is limited to a single byte.",
            "pcre2": " When this flag is present, ripgrep will use the PCRE2 regex engine instead of its default regex\nengine.  This is generally useful when you want to use features such as look-around or\nbackreferences.  Note that PCRE2 is an optional ripgrep feature. If PCRE2 wasn't included in your\nbuild of ripgrep, then using this flag will result in ripgrep printing an error message and exiting.\nPCRE2 may also have worse user experience in some cases, since it has fewer introspection APIs than\nripgrep's default regex engine. For example, if you use a ' in a PCRE2 regex without the\n'-U/--multiline' flag, then ripgrep will silently fail to match anything instead of reporting an\nerror immediately (like it does with the default regex engine).  Related flags: --no-pcre2-unicode\nThis flag can be disabled with --no-pcre2.",
            "pcre2_version": " When this flag is present, ripgrep will print the version of PCRE2 in use, along with other\ninformation, and then exit. If PCRE2 is not available, then ripgrep will print an error message and\nexit with an error code.",
            "pre": ' For each input FILE, search the standard output of COMMAND FILE rather than the contents of FILE.\nThis option expects the COMMAND program to either be an absolute path or to be available in your\nPATH. Either an empty string COMMAND or the \'--no-pre\' flag will disable this behavior.  WARNING:\nWhen this flag is set, ripgrep will unconditionally spawn a process for every file that is searched.\nTherefore, this can incur an unnecessarily large performance penalty if you don\'t otherwise need the\nflexibility offered by this flag. One possible mitigation to this is to use the \'--pre-glob\' flag to\nlimit which files a preprocessor is run with.  A preprocessor is not run when ripgrep is searching\nstdin.  When searching over sets of files that may require one of several decoders as preprocessors,\nCOMMAND should be a wrapper program or script which first classifies FILE based on magic\nnumbers/content or based on the FILE name and then dispatches to an appropriate preprocessor. Each\nCOMMAND also has its standard input connected to FILE for convenience.  For example, a shell script\nfor COMMAND might look like:  case "$1" in *.pdf) exec pdftotext "$1" - ;; *) case $(file "$1") in\n*Zstandard*) exec pzstd -cdq ;; *) exec cat ;; esac ;; esac  The above script uses `pdftotext` to\nconvert a PDF file to plain text. For all other files, the script uses the `file` utility to sniff\nthe type of the file based on its contents. If it is a compressed file in the Zstandard format, then\n`pzstd` is used to decompress the contents to stdout.  This overrides the -z/--search-zip flag.',
            "pretty": " This is a convenience alias for '--color always --heading --line-number'. This flag is useful when\nyou still want pretty output even if you're piping ripgrep to another program or file. For example:\n'rg -p foo | less -R'.",
            "quiet": " Do not print anything to stdout. If a match is found in a file, then ripgrep will stop searching.\nThis is useful when ripgrep is used only for its exit code (which will be an error if no matches are\nfound).  When --files is used, then ripgrep will stop finding files after finding the first file\nthat matches all ignore rules.",
            "regex_size_limit": " The upper size limit of the compiled regex. The default limit is 10M.  The argument accepts the\nsame size suffixes as allowed in the --max-filesize flag.",
            "regexp": " A pattern to search for. This option can be provided multiple times, where all patterns given are\nsearched. Lines matching at least one of the provided patterns are printed. This flag can also be\nused when searching for patterns that start with a dash.  For example, to search for the literal\n'-foo', you can use this flag:  rg -e -foo  You can also use the special '--' delimiter to indicate\nthat no more flags will be provided. Namely, the following is equivalent to the above:  rg -- -foo",
            "replace": " Replace every match with the text given when printing results. Neither this flag nor any other\nripgrep flag will modify your files.  Capture group indices (e.g., $5) and names (e.g., $foo) are\nsupported in the replacement string. Capture group indices are numbered based on the position of the\nopening parenthesis of the group, where the leftmost such group is $1. The special $0 group\ncorresponds to the entire match.  In shells such as Bash and zsh, you should wrap the pattern in\nsingle quotes instead of double quotes. Otherwise, capture group indices will be replaced by\nexpanded shell variables which will most likely be empty.  To write a literal '$', use '$$'.  Note\nthat the replacement by default replaces each match, and NOT the entire line. To replace the entire\nline, you should match the entire line.  This flag can be used with the -o/--only-matching flag.",
            "search_zip": " Search in compressed files. Currently gzip, bzip2, xz, LZ4, LZMA, Brotli and Zstd files are\nsupported. This option expects the decompression binaries to be available in your PATH.  This flag\ncan be disabled with --no-search-zip.",
            "smart_case": " Searches case insensitively if the pattern is all lowercase. Search case sensitively otherwise.  A\npattern is considered all lowercase if both of the following rules hold:  First, the pattern\ncontains at least one literal character. For example, 'a\\w' contains a literal ('a') but just '\\w'\ndoes not.  Second, of the literals in the pattern, none of them are considered to be uppercase\naccording to Unicode. For example, 'foo\\pL' has no uppercase literals but 'Foo\\pL' does.  This\noverrides the -s/--case-sensitive and -i/--ignore-case flags.",
            "sort": " This flag enables sorting of results in ascending order. The possible values for this flag are:\nnone      (Default) Do not sort results. Fastest. Can be multi-threaded. path      Sort by file\npath. Always single-threaded. modified  Sort by the last modified time on a file. Always single-\nthreaded. accessed  Sort by the last accessed time on a file. Always single-threaded. created   Sort\nby the creation time on a file. Always single-threaded.  If the chosen (manually or by-default)\nsorting criteria isn't available on your system (for example, creation time is not available on ext4\nfile systems), then ripgrep will attempt to detect this, print an error and exit without searching.\nTo sort results in reverse or descending order, use the --sortr flag. Also, this flag overrides\n--sortr.  Note that sorting results currently always forces ripgrep to abandon parallelism and run\nin a single thread.",
            "sortr": " This flag enables sorting of results in descending order. The possible values for this flag are:\nnone      (Default) Do not sort results. Fastest. Can be multi-threaded. path      Sort by file\npath. Always single-threaded. modified  Sort by the last modified time on a file. Always single-\nthreaded. accessed  Sort by the last accessed time on a file. Always single-threaded. created   Sort\nby the creation time on a file. Always single-threaded.  If the chosen (manually or by-default)\nsorting criteria isn't available on your system (for example, creation time is not available on ext4\nfile systems), then ripgrep will attempt to detect this, print an error and exit without searching.\nTo sort results in ascending order, use the --sort flag. Also, this flag overrides --sort.  Note\nthat sorting results currently always forces ripgrep to abandon parallelism and run in a single\nthread.",
            "stats": " Print aggregate statistics about this ripgrep search. When this flag is present, ripgrep will print\nthe following stats to stdout at the end of the search: number of matched lines, number of files\nwith matches, number of files searched, and the time taken for the entire search to complete.  This\nset of aggregate statistics may expand over time.  Note that this flag has no effect if --files,\n--files-with-matches or files-without-match is passed.  This flag can be disabled with --no-stats.",
            "text": " Search binary files as if they were text. When this flag is present, ripgrep's binary file\ndetection is disabled. This means that when a binary file is searched, its contents may be printed\nif there is a match. This may cause escape codes to be printed that alter the behavior of your\nterminal.  When binary file detection is enabled it is imperfect. In general, it uses a simple\nheuristic. If a NUL byte is seen during search, then the file is considered binary and search stops\n(unless this flag is present). Alternatively, if the '--binary' flag is used, then ripgrep will only\nquit when it sees a NUL byte after it sees a match (or searches the entire file).  This flag can be\ndisabled with '--no-text'. It overrides the '--binary' flag.",
            "threads": " The approximate number of threads to use. A value of 0 (which is the default) causes ripgrep to\nchoose the thread count using heuristics.",
            "trim": " When set, all ASCII whitespace at the beginning of each line printed will be trimmed.  This flag\ncan be disabled with --no-trim.",
            "type": " Only search files matching TYPE. Multiple type flags may be provided. Use the type-list flag to\nlist all available types.  This flag supports the special value 'all', which will behave as if\n--type was provided for every file type supported by ripgrep (including any custom file types). The\nend result is that '--type all' causes ripgrep to search in \"whitelist\" mode, where it will only\nsearch files it recognizes via its type definitions.",
            "type_add": " Add a new glob for a particular file type. Only one glob can be added at a time. Multiple --type-\nadd flags can be provided. Unless --type-clear is used, globs are added to any existing globs\ndefined inside of ripgrep.  Note that this MUST be passed to every invocation of ripgrep. Type\nsettings are NOT persisted. See CONFIGURATION FILES for a workaround.  Example:  rg --type-add\n'foo:*.foo' -tfoo PATTERN.  type-add can also be used to include rules from other types with the\nspecial include directive. The include directive permits specifying one or more other type names\n(separated by a comma) that have been defined and its rules will automatically be imported into the\ntype specified. For example, to create a type called src that matches C++, Python and Markdown\nfiles, one can use:  type-add 'src:include:cpp,py,md'  Additional glob rules can still be added to\nthe src type by using the type-add flag again:  type-add 'src:include:cpp,py,md' --type-add\n'src:*.foo'  Note that type names must consist only of Unicode letters or numbers. Punctuation\ncharacters are not allowed.",
            "type_clear": "  ... Clear the file type globs previously defined for TYPE. This only clears the default type\ndefinitions that are found inside of ripgrep.  Note that this MUST be passed to every invocation of\nripgrep. Type settings are NOT persisted. See CONFIGURATION FILES for a workaround.",
            "type_list": " Show all supported file types and their corresponding globs.",
            "type_not": "  ... Do not search files matching TYPE. Multiple type-not flags may be provided. Use the --type-\nlist flag to list all available types.",
            "unrestricted": " Reduce the level of \"smart\" searching. A single -u won't respect .gitignore (etc.) files (--no-\nignore). Two -u flags will additionally search hidden files and directories (-./--hidden). Three -u\nflags will additionally search binary files (--binary).  'rg -uuu' is roughly equivalent to 'grep\n-r'.",
            "version": " Prints version information",
            "vimgrep": " Show results with every match on its own line, including line numbers and column numbers. With this\noption, a line with more than one match will be printed more than once.",
            "with_filename": " Display the file path for matches. This is the default when more than one file is searched. If\n--heading is enabled (the default when printing to a terminal), the file path will be shown above\nclusters of matches from each file; otherwise, the file name will be shown as a prefix for each\nmatched line.  This flag overrides --no-filename.",
            "word_regexp": " Only show matches surrounded by word boundaries. This is roughly equivalent to putting \x08 before and\nafter all of the search patterns.  This overrides the --line-regexp flag.",
        }
        self.target_file_or_folder = []
        self.option_targetfile = option_targetfile
        self.join_parameters_dict = {}
        self.same_command_multiple_times = {"--regexp": ""}
        self.separador_for_multiple_arguments = "Ç"
        self.self_added_arguments = []
        self.last_command_line_called = []

    def add_python_variable_instead_of_file(self, variable: [bytes, str]):
        if isinstance(variable, str):
            variable = variable.encode()
        self.target_file_or_folder.append(variable)
        return self

    def add_target_file_or_folder(self, target_file_or_folder: Union[str, list]):
        if isinstance(target_file_or_folder, str):
            target_file_or_folder = [target_file_or_folder]
        self.target_file_or_folder.extend(target_file_or_folder)
        return self

    def reset_options(self):
        for key in list(self.execute_dict.keys()):
            self.execute_dict[key] = False
        self.self_added_arguments = []
        return self

    def print_options_to_screen(self):
        for help, exe in zip(self.helpdict.items(), self.execute_dict.items()):
            key_h, item_h = help
            key_e, item_e = exe
            print(f"""Parameter:\t\t\t{key_e} {key_h}""")
            print(f"""Current Settings:\t\t{item_e} """)
            print(f"""Information:\t\t{item_h}""")

            print(
                "---------------------------------------------------------------------------------------------"
            )
        print(f"""Self Added Arguments:\t\tf{self.self_added_arguments}""")
        return self

    def run(
        self,
        capture_output: bool = True,
        save_output_with_shell: Union[None, str] = None,
    ):
        self.last_command_line_called = []
        regexlist = []
        add_to_search = [
            (
                re.sub(rf"{self.separador_for_multiple_arguments}\d*$", "", x[0]),
                str(x[1]),
                x[1],
            )
            for x in self.execute_dict.items()
            if x[1] is not False
        ]
        add_to_search_list = []
        for key, item, real_value in add_to_search:
            print(key, item)
            if isinstance(real_value, bool):

                add_to_search_list.append([key])
            else:
                if key in self.join_parameters_dict:
                    add_to_search_list.append([f"{key}{item}"])
                else:
                    add_to_search_list.append([key, item])

        regexlist.extend(add_to_search_list)
        regexlist = self.necessary_beginning + regexlist + self.self_added_arguments
        regexlist = PyRipGREP.flatten_iter(regexlist)
        if self.option_targetfile is not None:
            regexlist.append(self.option_targetfile)
        if self.target_file_or_folder:
            if isinstance(self.target_file_or_folder[0], str):
                regexlist.extend(self.target_file_or_folder)
            else:
                f = tempfile()
                f.write(self.target_file_or_folder[0])
                f.seek(0)
                ergebnis = subprocess.run(regexlist, stdin=f, capture_output=True)
                f.close()
                self.last_command_line_called = regexlist.copy()
                return ergebnis

        if save_output_with_shell is not None:
            regexlist.append(">>")
            regexlist.append(save_output_with_shell)
            ergebnis = subprocess.run(
                regexlist, capture_output=capture_output, shell=True
            )
        else:
            ergebnis = subprocess.run(regexlist, capture_output=capture_output)
        self.last_command_line_called = regexlist.copy()
        return ergebnis

    def add_own_parameter_or_option(self, values):
        if not isinstance(values, (list, tuple)):
            values = [values]
        values = self.flatten_iter(values)
        self.self_added_arguments.extend(values)
        return self

    @staticmethod
    def _delete_duplicates_from_nested_list(nestedlist):
        tempstringlist = {}
        for ergi in nestedlist:
            tempstringlist[str(ergi)] = ergi
        endliste = [tempstringlist[key] for key in tempstringlist.keys()]
        return endliste.copy()

    @staticmethod
    def flatten_iter(iterable):
        def iter_flatten(iterable):
            it = iter(iterable)
            for e in it:
                if isinstance(e, (list, tuple)):
                    for f in iter_flatten(e):
                        yield f
                else:
                    yield e

        a = [
            i if not isinstance(i, (str, int, float)) else [i]
            for i in iter_flatten(iterable)
        ]
        a = [i for i in iter_flatten(a)]
        return a

    def _handle_multiple_times_same_flag(self, key_to_check, value_to_set):
        are_there_more = True
        startvalue = 0
        keytocheck = ""
        while are_there_more:
            keytocheck = (
                f"{key_to_check}"
                + self.separador_for_multiple_arguments
                + str(startvalue)
            )
            if not keytocheck in self.execute_dict:
                are_there_more = False
            else:
                if isinstance(value_to_set, bool):
                    if value_to_set is False:
                        self.execute_dict[keytocheck] = value_to_set
                startvalue = startvalue + 1
        if keytocheck not in self.execute_dict:
            if isinstance(value_to_set, bool):
                if value_to_set is False:
                    return
            self.execute_dict[keytocheck] = value_to_set

    def _print_option_activate_warning(self):
        pass

    def after_context(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Show NUM lines after each match.  This overrides the --context and --passthru flags."""
        if get_help:
            print(self.helpdict["after_context"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--after-context"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--after-context", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--after-context"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--after-context"] is False and not multi_allowed:
                self.execute_dict["--after-context"] = option
            varformulti = option
        else:
            self.execute_dict["--after-context"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--after-context", value_to_set=varformulti
            )
        return self

    def auto_hybrid_regex(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """DEPRECATED. Use --engine instead.  When this flag is used, ripgrep will dynamically choose between
        supported regex engines depending on the features used in a pattern. When ripgrep chooses a regex
        engine, it applies that choice for every regex provided to ripgrep (e.g., via multiple -e/--regexp
        or -f/--file flags).  As an example of how this flag might behave, ripgrep will attempt to use its
        default finite automata based regex engine whenever the pattern can be successfully compiled with
        that regex engine. If PCRE2 is enabled and if the pattern given could not be compiled with the
        default regex engine, then PCRE2 will be automatically used for searching. If PCRE2 isn't available,
        then this flag has no effect because there is only one regex engine to choose from.  In the future,
        ripgrep may adjust its heuristics for how it decides which regex engine to use. In general, the
        heuristics will be limited to a static analysis of the patterns, and not to any specific runtime
        behavior observed while searching files.  The primary downside of using this flag is that it may not
        always be obvious which regex engine ripgrep uses, and thus, the match semantics or performance
        profile of ripgrep may subtly and unexpectedly change. However, in many cases, all regex engines
        will agree on what constitutes a match and it can be nice to transparently support more advanced
        regex features like look-around and backreferences without explicitly needing to enable them.  This
        flag can be disabled with --no-auto-hybrid-regex."""
        if get_help:
            print(self.helpdict["auto_hybrid_regex"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--auto-hybrid-regex"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--auto-hybrid-regex", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--auto-hybrid-regex"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--auto-hybrid-regex"] is False and not multi_allowed:
                self.execute_dict["--auto-hybrid-regex"] = option
            varformulti = option
        else:
            self.execute_dict["--auto-hybrid-regex"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--auto-hybrid-regex", value_to_set=varformulti
            )
        return self

    def before_context(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Show NUM lines before each match.  This overrides the --context and --passthru flags."""
        if get_help:
            print(self.helpdict["before_context"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--before-context"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--before-context", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--before-context"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--before-context"] is False and not multi_allowed:
                self.execute_dict["--before-context"] = option
            varformulti = option
        else:
            self.execute_dict["--before-context"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--before-context", value_to_set=varformulti
            )
        return self

    def binary(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Enabling this flag will cause ripgrep to search binary files. By default, ripgrep attempts to
        automatically skip binary files in order to improve the relevance of results and make the search
        faster.  Binary files are heuristically detected based on whether they contain a NUL byte or not. By
        default (without this flag set), once a NUL byte is seen, ripgrep will stop searching the file.
        Usually, NUL bytes occur in the beginning of most binary files. If a NUL byte occurs after a match,
        then ripgrep will still stop searching the rest of the file, but a warning will be printed.  In
        contrast, when this flag is provided, ripgrep will continue searching a file even if a NUL byte is
        found. In particular, if a NUL byte is found then ripgrep will continue searching until either a
        match is found or the end of the file is reached, whichever comes sooner. If a match is found, then
        ripgrep will stop and print a warning saying that the search stopped prematurely.  If you want
        ripgrep to search a file without any special NUL byte handling at all (and potentially print binary
        data to stdout), then you should use the '-a/--text' flag.  The '--binary' flag is a flag for
        controlling ripgrep's automatic filtering mechanism. As such, it does not need to be used when
        searching a file explicitly or when searching stdin. That is, it is only applicable when recursively
        searching a directory.  Note that when the '-u/--unrestricted' flag is provided for a third time,
        then this flag is automatically enabled.  This flag can be disabled with '--no-binary'. It overrides
        the '-a/--text' flag."""
        if get_help:
            print(self.helpdict["binary"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--binary"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--binary", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--binary"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--binary"] is False and not multi_allowed:
                self.execute_dict["--binary"] = option
            varformulti = option
        else:
            self.execute_dict["--binary"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--binary", value_to_set=varformulti
            )
        return self

    def block_buffered(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """When enabled, ripgrep will use block buffering. That is, whenever a matching line is found, it will
        be written to an in-memory buffer and will not be written to stdout until the buffer reaches a
        certain size. This is the default when ripgrep's stdout is redirected to a pipeline or a file. When
        ripgrep's stdout is connected to a terminal, line buffering will be used. Forcing block buffering
        can be useful when dumping a large amount of contents to a terminal.  Forceful block buffering can
        be disabled with --no-block-buffered. Note that using --no-block-buffered causes ripgrep to revert
        to its default behavior of automatically detecting the buffering strategy. To force line buffering,
        use the --line-buffered flag."""
        if get_help:
            print(self.helpdict["block_buffered"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--block-buffered"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--block-buffered", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--block-buffered"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--block-buffered"] is False and not multi_allowed:
                self.execute_dict["--block-buffered"] = option
            varformulti = option
        else:
            self.execute_dict["--block-buffered"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--block-buffered", value_to_set=varformulti
            )
        return self

    def byte_offset(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Print the 0-based byte offset within the input file before each line of output. If -o (--only-
        matching) is specified, print the offset of the matching part itself.  If ripgrep does transcoding,
        then the byte offset is in terms of the the result of transcoding and not the original data. This
        applies similarly to another transformation on the source, such as decompression or a --pre filter.
        Note that when the PCRE2 regex engine is used, then UTF-8 transcoding is done by default."""
        if get_help:
            print(self.helpdict["byte_offset"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--byte-offset"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--byte-offset", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--byte-offset"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--byte-offset"] is False and not multi_allowed:
                self.execute_dict["--byte-offset"] = option
            varformulti = option
        else:
            self.execute_dict["--byte-offset"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--byte-offset", value_to_set=varformulti
            )
        return self

    def case_sensitive(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Search case sensitively.  This overrides the -i/--ignore-case and -S/--smart-case flags."""
        if get_help:
            print(self.helpdict["case_sensitive"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--case-sensitive"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--case-sensitive", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--case-sensitive"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--case-sensitive"] is False and not multi_allowed:
                self.execute_dict["--case-sensitive"] = option
            varformulti = option
        else:
            self.execute_dict["--case-sensitive"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--case-sensitive", value_to_set=varformulti
            )
        return self

    def color(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """This flag controls when to use colors. The default setting is 'auto', which means ripgrep will try
        to guess when to use colors. For example, if ripgrep is printing to a terminal, then it will use
        colors, but if it is redirected to a file or a pipe, then it will suppress color output. ripgrep
        will suppress color output in some other circumstances as well. For example, if the TERM environment
        search_in is not set or set to 'dumb', then ripgrep will not use colors.  The possible values for
        this flag are:  never    Colors will never be used. auto     The default. ripgrep tries to be smart.
        always   Colors will always be used regardless of where output is sent. ansi     Like 'always', but
        emits ANSI escapes (even in a Windows console).  When the --vimgrep flag is given to ripgrep, then
        the default value for the color flag changes to 'never'."""
        if get_help:
            print(self.helpdict["color"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--color"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--color", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--color"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--color"] is False and not multi_allowed:
                self.execute_dict["--color"] = option
            varformulti = option
        else:
            self.execute_dict["--color"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--color", value_to_set=varformulti
            )
        return self

    def colors(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """This flag specifies color settings for use in the output. This flag may be provided multiple times.
        Settings are applied iteratively. Colors are limited to one of eight choices: red, blue, green,
        cyan, magenta, yellow, white and black. Styles are limited to nobold, bold, nointense, intense,
        nounderline or underline.  The format of the flag is '{type}:{attribute}:{value}'. '{type}' should
        be one of path, line, column or match. '{attribute}' can be fg, bg or style. '{value}' is either a
        color (for fg and bg) or a text style. A special format, '{type}:none', will clear all color
        settings for '{type}'.  For example, the following command will change the match color to magenta
        and the background color for line numbers to yellow:  rg --colors 'match:fg:magenta' --colors
        'line:bg:yellow' foo.  Extended colors can be used for '{value}' when the terminal supports ANSI
        color sequences. These are specified as either 'x' (256-color) or 'x,x,x' (24-bit truecolor) where x
        is a number between 0 and 255 inclusive. x may be given as a normal decimal number or a hexadecimal
        number, which is prefixed by `0x`.  For example, the following command will change the match
        background color to that represented by the rgb value (0,128,255):  rg --colors 'match:bg:0,128,255'
        or, equivalently,  rg --colors 'match:bg:0x0,0x80,0xFF'  Note that the the intense and nointense
        style flags will have no effect when used alongside these extended color codes."""
        if get_help:
            print(self.helpdict["colors"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--colors"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--colors", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--colors"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--colors"] is False and not multi_allowed:
                self.execute_dict["--colors"] = option
            varformulti = option
        else:
            self.execute_dict["--colors"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--colors", value_to_set=varformulti
            )
        return self

    def column(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Show column numbers (1-based). This only shows the column numbers for the first match on each line.
        This does not try to account for Unicode. One byte is equal to one column. This implies --line-
        number.  This flag can be disabled with --no-column."""
        if get_help:
            print(self.helpdict["column"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--column"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--column", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--column"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--column"] is False and not multi_allowed:
                self.execute_dict["--column"] = option
            varformulti = option
        else:
            self.execute_dict["--column"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--column", value_to_set=varformulti
            )
        return self

    def context(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Show NUM lines before and after each match. This is equivalent to providing both the -B/--before-
        context and -A/--after-context flags with the same value.  This overrides both the -B/--before-
        context and -A/--after-context flags, in addition to the --passthru flag."""
        if get_help:
            print(self.helpdict["context"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--context"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--context", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--context"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--context"] is False and not multi_allowed:
                self.execute_dict["--context"] = option
            varformulti = option
        else:
            self.execute_dict["--context"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--context", value_to_set=varformulti
            )
        return self

    def context_separator(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """The string used to separate non-contiguous context lines in the output. This is only used when one
        of the context flags is used (-A, -B or -C). Escape sequences like  or      may be used. The
        default value is --.  When the context separator is set to an empty string, then a line break is
        still inserted. To completely disable context separators, use the no-context-separator flag."""
        if get_help:
            print(self.helpdict["context_separator"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--context-separator"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--context-separator", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--context-separator"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--context-separator"] is False and not multi_allowed:
                self.execute_dict["--context-separator"] = option
            varformulti = option
        else:
            self.execute_dict["--context-separator"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--context-separator", value_to_set=varformulti
            )
        return self

    def count(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """This flag suppresses normal output and shows the number of lines that match the given patterns for
        each file searched. Each file containing a match has its path and count printed on each line. Note
        that this reports the number of lines that match and not the total number of matches, unless
        -U/--multiline is enabled. In multiline mode, --count is equivalent to --count-matches.  If only one
        file is given to ripgrep, then only the count is printed if there is a match. The --with-filename
        flag can be used to force printing the file path in this case. If you need a count to be printed
        regardless of whether there is a match, then use --include-zero.  This overrides the --count-matches
        flag. Note that when --count is combined with --only-matching, then ripgrep behaves as if --count-
        matches was given."""
        if get_help:
            print(self.helpdict["count"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--count"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--count", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--count"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--count"] is False and not multi_allowed:
                self.execute_dict["--count"] = option
            varformulti = option
        else:
            self.execute_dict["--count"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--count", value_to_set=varformulti
            )
        return self

    def count_matches(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """This flag suppresses normal output and shows the number of individual matches of the given patterns
        for each file searched. Each file containing matches has its path and match count printed on each
        line. Note that this reports the total number of individual matches and not the number of lines that
        match.  If only one file is given to ripgrep, then only the count is printed if there is a match.
        The --with-filename flag can be used to force printing the file path in this case.  This overrides
        the --count flag. Note that when --count is combined with only-matching, then ripgrep behaves as if
        --count-matches was given."""
        if get_help:
            print(self.helpdict["count_matches"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--count-matches"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--count-matches", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--count-matches"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--count-matches"] is False and not multi_allowed:
                self.execute_dict["--count-matches"] = option
            varformulti = option
        else:
            self.execute_dict["--count-matches"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--count-matches", value_to_set=varformulti
            )
        return self

    def crlf(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """When enabled, ripgrep will treat CRLF (') as a line terminator instead of just '.  Principally,
        this permits '$' in regex patterns to match just before CRLF instead of just before LF. The
        underlying regex engine may not support this natively, so ripgrep will translate all instances of
        '$' to '(?:??$)'. This may produce slightly different than desired match offsets. It is intended as
        a work-around until the regex engine supports this natively.  CRLF support can be disabled with
        --no-crlf."""
        if get_help:
            print(self.helpdict["crlf"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--crlf"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--crlf", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--crlf"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--crlf"] is False and not multi_allowed:
                self.execute_dict["--crlf"] = option
            varformulti = option
        else:
            self.execute_dict["--crlf"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--crlf", value_to_set=varformulti
            )
        return self

    def debug(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Show debug messages. Please use this when filing a bug report.  The --debug flag is generally
        useful for figuring out why ripgrep skipped searching a particular file. The debug messages should
        mention all files skipped and why they were skipped.  To get even more debug output, use the --trace
        flag, which implies --debug along with additional trace data. With --trace, the output could be
        quite large and is generally more useful for development."""
        if get_help:
            print(self.helpdict["debug"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--debug"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--debug", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--debug"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--debug"] is False and not multi_allowed:
                self.execute_dict["--debug"] = option
            varformulti = option
        else:
            self.execute_dict["--debug"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--debug", value_to_set=varformulti
            )
        return self

    def dfa_size_limit(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """The upper size limit of the regex DFA. The default limit is 10M. This should only be changed on
        very large regex inputs where the (slower) fallback regex engine may otherwise be used if the limit
        is reached.  The argument accepts the same size suffixes as allowed in with the max-filesize flag."""
        if get_help:
            print(self.helpdict["dfa_size_limit"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--dfa-size-limit"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--dfa-size-limit", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--dfa-size-limit"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--dfa-size-limit"] is False and not multi_allowed:
                self.execute_dict["--dfa-size-limit"] = option
            varformulti = option
        else:
            self.execute_dict["--dfa-size-limit"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--dfa-size-limit", value_to_set=varformulti
            )
        return self

    def encoding(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Specify the text encoding that ripgrep will use on all files searched. The default value is 'auto',
        which will cause ripgrep to do a best effort automatic detection of encoding on a per-file basis.
        Automatic detection in this case only applies to files that begin with a UTF-8 or UTF-16 byte-order
        mark (BOM). No other automatic detection is performed. One can also specify 'none' which will then
        completely disable BOM sniffing and always result in searching the raw bytes, including a BOM if
        it's present, regardless of its encoding.  Other supported values can be found in the list of labels
        here: https://encoding.spec.whatwg.org/#concept-encoding-get  For more details on encoding and how
        ripgrep deals with it, see GUIDE.md.  This flag can be disabled with --no-encoding."""
        if get_help:
            print(self.helpdict["encoding"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--encoding"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--encoding", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--encoding"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--encoding"] is False and not multi_allowed:
                self.execute_dict["--encoding"] = option
            varformulti = option
        else:
            self.execute_dict["--encoding"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--encoding", value_to_set=varformulti
            )
        return self

    def engine(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Specify which regular expression engine to use. When you choose a regex engine, it applies that
        choice for every regex provided to ripgrep (e.g., via multiple -e/--regexp or -f/--file flags).
        Accepted values are 'default', 'pcre2', or 'auto'.  The default value is 'default', which is the
        fastest and should be good for most use cases. The 'pcre2' engine is generally useful when you want
        to use features such as look-around or backreferences. 'auto' will dynamically choose between
        supported regex engines depending on the features used in a pattern on a best effort basis.  Note
        that the 'pcre2' engine is an optional ripgrep feature. If PCRE2 wasn't included in your build of
        ripgrep, then using this flag will result in ripgrep printing an error message and exiting.  This
        overrides previous uses of --pcre2 and --auto-hybrid-regex flags. [default: default]"""
        if get_help:
            print(self.helpdict["engine"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--engine"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--engine", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--engine"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--engine"] is False and not multi_allowed:
                self.execute_dict["--engine"] = option
            varformulti = option
        else:
            self.execute_dict["--engine"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--engine", value_to_set=varformulti
            )
        return self

    def field_context_separator(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Set the field context separator, which is used to delimit file paths, line numbers, columns and the
        context itself, when printing contextual lines. The separator may be any number of bytes, including
        zero. Escape sequences like  or        may be used. The default value is -."""
        if get_help:
            print(self.helpdict["field_context_separator"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--field-context-separator"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--field-context-separator", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--field-context-separator"] = True
            varformulti = True

        elif option is not None and activated:
            if (
                self.execute_dict["--field-context-separator"] is False
                and not multi_allowed
            ):
                self.execute_dict["--field-context-separator"] = option
            varformulti = option
        else:
            self.execute_dict["--field-context-separator"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--field-context-separator", value_to_set=varformulti
            )
        return self

    def field_match_separator(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Set the field match separator, which is used to delimit file paths, line numbers, columns and the
        match itself. The separator may be any number of bytes, including zero. Escape sequences like  or
        may be used. The default value is -."""
        if get_help:
            print(self.helpdict["field_match_separator"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--field-match-separator"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--field-match-separator", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--field-match-separator"] = True
            varformulti = True

        elif option is not None and activated:
            if (
                self.execute_dict["--field-match-separator"] is False
                and not multi_allowed
            ):
                self.execute_dict["--field-match-separator"] = option
            varformulti = option
        else:
            self.execute_dict["--field-match-separator"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--field-match-separator", value_to_set=varformulti
            )
        return self

    def file(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Search for patterns from the given file, with one pattern per line. When this flag is used multiple
        times or in combination with the -e/--regexp flag, then all patterns provided are searched. Empty
        pattern lines will match all input lines, and the newline is not counted as part of the pattern.  A
        line is printed if and only if it matches at least one of the patterns."""
        if get_help:
            print(self.helpdict["file"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--file"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--file", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--file"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--file"] is False and not multi_allowed:
                self.execute_dict["--file"] = option
            varformulti = option
        else:
            self.execute_dict["--file"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--file", value_to_set=varformulti
            )
        return self

    def files(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Print each file that would be searched without actually performing the search. This is useful to
        determine whether a particular file is being searched or not."""
        if get_help:
            print(self.helpdict["files"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--files"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--files", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--files"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--files"] is False and not multi_allowed:
                self.execute_dict["--files"] = option
            varformulti = option
        else:
            self.execute_dict["--files"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--files", value_to_set=varformulti
            )
        return self

    def files_with_matches(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Print the paths with at least one match and suppress match contents.  This overrides --files-
        without-match."""
        if get_help:
            print(self.helpdict["files_with_matches"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--files-with-matches"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--files-with-matches", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--files-with-matches"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--files-with-matches"] is False and not multi_allowed:
                self.execute_dict["--files-with-matches"] = option
            varformulti = option
        else:
            self.execute_dict["--files-with-matches"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--files-with-matches", value_to_set=varformulti
            )
        return self

    def files_without_match(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Print the paths that contain zero matches and suppress match contents. This inverts/negates the
        --files-with-matches flag.  This overrides --files-with-matches."""
        if get_help:
            print(self.helpdict["files_without_match"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--files-without-match"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--files-without-match", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--files-without-match"] = True
            varformulti = True

        elif option is not None and activated:
            if (
                self.execute_dict["--files-without-match"] is False
                and not multi_allowed
            ):
                self.execute_dict["--files-without-match"] = option
            varformulti = option
        else:
            self.execute_dict["--files-without-match"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--files-without-match", value_to_set=varformulti
            )
        return self

    def fixed_strings(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Treat the pattern as a literal string instead of a regular expression. When this flag is used,
        special regular expression meta characters such as .(){}*+ do not need to be escaped.  This flag can
        be disabled with --no-fixed-strings."""
        if get_help:
            print(self.helpdict["fixed_strings"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--fixed-strings"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--fixed-strings", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--fixed-strings"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--fixed-strings"] is False and not multi_allowed:
                self.execute_dict["--fixed-strings"] = option
            varformulti = option
        else:
            self.execute_dict["--fixed-strings"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--fixed-strings", value_to_set=varformulti
            )
        return self

    def follow(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """When this flag is enabled, ripgrep will follow symbolic links while traversing directories. This is
        disabled by default. Note that ripgrep will check for symbolic link loops and report errors if it
        finds one.  This flag can be disabled with --no-follow."""
        if get_help:
            print(self.helpdict["follow"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--follow"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--follow", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--follow"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--follow"] is False and not multi_allowed:
                self.execute_dict["--follow"] = option
            varformulti = option
        else:
            self.execute_dict["--follow"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--follow", value_to_set=varformulti
            )
        return self

    def glob(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Include or exclude files and directories for searching that match the given glob. This always
        overrides any other ignore logic. Multiple glob flags may be used. Globbing rules match .gitignore
        globs. Precede a glob with a ! to exclude it. If multiple globs match a file or directory, the glob
        given later in the command line takes precedence.  As an extension, globs support specifying
        alternatives: *-g ab{c,d}* is equivalet to *-g abc -g abd*. Empty alternatives like *-g ab{,c}* are
        not currently supported. Note that this syntax extension is also currently enabled in gitignore
        files, even though this syntax isn't supported by git itself. ripgrep may disable this syntax
        extension in gitignore files, but it will always remain available via the -g/--glob flag.  When this
        flag is set, every file and directory is applied to it to test for a match. So for example, if you
        only want to search in a particular directory 'foo', then *-g foo* is incorrect because 'foo/bar'
        does not match the glob 'foo'. Instead, you should use *-g 'foo/**'*."""
        if get_help:
            print(self.helpdict["glob"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--glob"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--glob", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--glob"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--glob"] is False and not multi_allowed:
                self.execute_dict["--glob"] = option
            varformulti = option
        else:
            self.execute_dict["--glob"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--glob", value_to_set=varformulti
            )
        return self

    def glob_case_insensitive(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Process glob patterns given with the -g/--glob flag case insensitively. This effectively treats
        --glob as --iglob.  This flag can be disabled with the --no-glob-case-insensitive flag."""
        if get_help:
            print(self.helpdict["glob_case_insensitive"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--glob-case-insensitive"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--glob-case-insensitive", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--glob-case-insensitive"] = True
            varformulti = True

        elif option is not None and activated:
            if (
                self.execute_dict["--glob-case-insensitive"] is False
                and not multi_allowed
            ):
                self.execute_dict["--glob-case-insensitive"] = option
            varformulti = option
        else:
            self.execute_dict["--glob-case-insensitive"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--glob-case-insensitive", value_to_set=varformulti
            )
        return self

    def help(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Prints help information. Use --help for more details."""
        if get_help:
            print(self.helpdict["help"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--help"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--help", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--help"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--help"] is False and not multi_allowed:
                self.execute_dict["--help"] = option
            varformulti = option
        else:
            self.execute_dict["--help"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--help", value_to_set=varformulti
            )
        return self

    def heading(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """This flag prints the file path above clusters of matches from each file instead of printing the
        file path as a prefix for each matched line. This is the default mode when printing to a terminal.
        This overrides the --no-heading flag."""
        if get_help:
            print(self.helpdict["heading"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--heading"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--heading", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--heading"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--heading"] is False and not multi_allowed:
                self.execute_dict["--heading"] = option
            varformulti = option
        else:
            self.execute_dict["--heading"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--heading", value_to_set=varformulti
            )
        return self

    def hidden(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Search hidden files and directories. By default, hidden files and directories are skipped. Note
        that if a hidden file or a directory is whitelisted in an ignore file, then it will be searched even
        if this flag isn't provided.  A file or directory is considered hidden if its base name starts with
        a dot character ('.'). On operating systems which support a `hidden` file attribute, like Windows,
        files with this attribute are also considered hidden.  This flag can be disabled with --no-hidden."""
        if get_help:
            print(self.helpdict["hidden"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--hidden"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--hidden", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--hidden"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--hidden"] is False and not multi_allowed:
                self.execute_dict["--hidden"] = option
            varformulti = option
        else:
            self.execute_dict["--hidden"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--hidden", value_to_set=varformulti
            )
        return self

    def iglob(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Include or exclude files and directories for searching that match the given glob. This always
        overrides any other ignore logic. Multiple glob flags may be used. Globbing rules match .gitignore
        globs. Precede a glob with a ! to exclude it. Globs are matched case insensitively."""
        if get_help:
            print(self.helpdict["iglob"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--iglob"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--iglob", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--iglob"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--iglob"] is False and not multi_allowed:
                self.execute_dict["--iglob"] = option
            varformulti = option
        else:
            self.execute_dict["--iglob"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--iglob", value_to_set=varformulti
            )
        return self

    def ignore_case(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """When this flag is provided, the given patterns will be searched case insensitively. The case
        insensitivity rules used by ripgrep conform to Unicode's "simple" case folding rules.  This flag
        overrides -s/--case-sensitive and -S/--smart-case."""
        if get_help:
            print(self.helpdict["ignore_case"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--ignore-case"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--ignore-case", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--ignore-case"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--ignore-case"] is False and not multi_allowed:
                self.execute_dict["--ignore-case"] = option
            varformulti = option
        else:
            self.execute_dict["--ignore-case"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--ignore-case", value_to_set=varformulti
            )
        return self

    def ignore_file(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Specifies a path to one or more .gitignore format rules files. These patterns are applied after the
        patterns found in .gitignore and .ignore are applied and are matched relative to the current working
        directory. Multiple additional ignore files can be specified by using the --ignore-file flag several
        times. When specifying multiple ignore files, earlier files have lower precedence than later files.
        If you are looking for a way to include or exclude files and directories directly on the command
        line, then used -g instead."""
        if get_help:
            print(self.helpdict["ignore_file"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--ignore-file"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--ignore-file", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--ignore-file"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--ignore-file"] is False and not multi_allowed:
                self.execute_dict["--ignore-file"] = option
            varformulti = option
        else:
            self.execute_dict["--ignore-file"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--ignore-file", value_to_set=varformulti
            )
        return self

    def ignore_file_case_insensitive(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Process ignore files (.gitignore, .ignore, etc.) case insensitively. Note that this comes with a
        performance penalty and is most useful on case insensitive file systems (such as Windows).  This
        flag can be disabled with the --no-ignore-file-case-insensitive flag."""
        if get_help:
            print(self.helpdict["ignore_file_case_insensitive"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--ignore-file-case-insensitive"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--ignore-file-case-insensitive", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--ignore-file-case-insensitive"] = True
            varformulti = True

        elif option is not None and activated:
            if (
                self.execute_dict["--ignore-file-case-insensitive"] is False
                and not multi_allowed
            ):
                self.execute_dict["--ignore-file-case-insensitive"] = option
            varformulti = option
        else:
            self.execute_dict["--ignore-file-case-insensitive"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--ignore-file-case-insensitive", value_to_set=varformulti
            )
        return self

    def include_zero(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """When used with --count or --count-matches, print the number of matches for each file even if there
        were zero matches. This is disabled by default but can be enabled to make ripgrep behave more like
        grep."""
        if get_help:
            print(self.helpdict["include_zero"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--include-zero"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--include-zero", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--include-zero"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--include-zero"] is False and not multi_allowed:
                self.execute_dict["--include-zero"] = option
            varformulti = option
        else:
            self.execute_dict["--include-zero"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--include-zero", value_to_set=varformulti
            )
        return self

    def invert_match(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Invert matching. Show lines that do not match the given patterns."""
        if get_help:
            print(self.helpdict["invert_match"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--invert-match"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--invert-match", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--invert-match"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--invert-match"] is False and not multi_allowed:
                self.execute_dict["--invert-match"] = option
            varformulti = option
        else:
            self.execute_dict["--invert-match"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--invert-match", value_to_set=varformulti
            )
        return self

    def json(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Enable printing results in a JSON Lines format.  When this flag is provided, ripgrep will emit a
        sequence of messages, each encoded as a JSON object, where there are five different message types:
        **begin** - A message that indicates a file is being searched and contains at least one match.
        **end** - A message the indicates a file is done being searched. This message also include summary
        statistics about the search for a particular file.  **match** - A message that indicates a match was
        found. This includes the text and offsets of the match.  **context** - A message that indicates a
        contextual line was found. This includes the text of the line, along with any match information if
        the search was inverted.  **summary** - The final message emitted by ripgrep that contains summary
        statistics about the search across all files.  Since file paths or the contents of files are not
        guaranteed to be valid UTF-8 and JSON itself must be representable by a Unicode encoding, ripgrep
        will emit all data elements as objects with one of two keys: 'text' or 'bytes'. 'text' is a normal
        JSON string when the data is valid UTF-8 while 'bytes' is the base64 encoded contents of the data.
        The JSON Lines format is only supported for showing search results. It cannot be used with other
        flags that emit other types of output, such as --files, files-with-matches, --files-without-match,
        --count or --count-matches. ripgrep will report an error if any of the aforementioned flags are used
        in concert with --json.  Other flags that control aspects of the standard output such as only-
        matching, --heading, --replace, --max-columns, etc., have no effect when --json is set.  A more
        complete description of the JSON format used can be found here: https://docs.rs/grep-
        printer/*/grep_printer/struct.JSON.html  The JSON Lines format can be disabled with --no-json."""
        if get_help:
            print(self.helpdict["json"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--json"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--json", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--json"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--json"] is False and not multi_allowed:
                self.execute_dict["--json"] = option
            varformulti = option
        else:
            self.execute_dict["--json"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--json", value_to_set=varformulti
            )
        return self

    def line_buffered(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """When enabled, ripgrep will use line buffering. That is, whenever a matching line is found, it will
        be flushed to stdout immediately. This is the default when ripgrep's stdout is connected to a
        terminal, but otherwise, ripgrep will use block buffering, which is typically faster. This flag
        forces ripgrep to use line buffering even if it would otherwise use block buffering. This is
        typically useful in shell pipelines, e.g., 'tail -f something.log | rg foo --line-buffered | rg
        bar'.  Forceful line buffering can be disabled with --no-line-buffered. Note that using --no-line-
        buffered causes ripgrep to revert to its default behavior of automatically detecting the buffering
        strategy. To force block buffering, use the --block-buffered flag."""
        if get_help:
            print(self.helpdict["line_buffered"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--line-buffered"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--line-buffered", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--line-buffered"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--line-buffered"] is False and not multi_allowed:
                self.execute_dict["--line-buffered"] = option
            varformulti = option
        else:
            self.execute_dict["--line-buffered"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--line-buffered", value_to_set=varformulti
            )
        return self

    def line_number(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Show line numbers (1-based). This is enabled by default when searching in a terminal."""
        if get_help:
            print(self.helpdict["line_number"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--line-number"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--line-number", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--line-number"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--line-number"] is False and not multi_allowed:
                self.execute_dict["--line-number"] = option
            varformulti = option
        else:
            self.execute_dict["--line-number"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--line-number", value_to_set=varformulti
            )
        return self

    def line_regexp(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Only show matches surrounded by line boundaries. This is equivalent to putting ^...$ around all of
        the search patterns. In other words, this only prints lines where the entire line participates in a
        match.  This overrides the --word-regexp flag."""
        if get_help:
            print(self.helpdict["line_regexp"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--line-regexp"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--line-regexp", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--line-regexp"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--line-regexp"] is False and not multi_allowed:
                self.execute_dict["--line-regexp"] = option
            varformulti = option
        else:
            self.execute_dict["--line-regexp"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--line-regexp", value_to_set=varformulti
            )
        return self

    def max_columns(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Don't print lines longer than this limit in bytes. Longer lines are omitted, and only the number of
        matches in that line is printed.  When this flag is omitted or is set to 0, then it has no effect."""
        if get_help:
            print(self.helpdict["max_columns"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--max-columns"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--max-columns", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--max-columns"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--max-columns"] is False and not multi_allowed:
                self.execute_dict["--max-columns"] = option
            varformulti = option
        else:
            self.execute_dict["--max-columns"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--max-columns", value_to_set=varformulti
            )
        return self

    def max_columns_preview(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """When the '--max-columns' flag is used, ripgrep will by default completely replace any line that is
        too long with a message indicating that a matching line was removed. When this flag is combined with
        '--max-columns', a preview of the line (corresponding to the limit size) is shown instead, where the
        part of the line exceeding the limit is not shown.  If the '--max-columns' flag is not set, then
        this has no effect.  This flag can be disabled with '--no-max-columns-preview'."""
        if get_help:
            print(self.helpdict["max_columns_preview"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--max-columns-preview"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--max-columns-preview", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--max-columns-preview"] = True
            varformulti = True

        elif option is not None and activated:
            if (
                self.execute_dict["--max-columns-preview"] is False
                and not multi_allowed
            ):
                self.execute_dict["--max-columns-preview"] = option
            varformulti = option
        else:
            self.execute_dict["--max-columns-preview"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--max-columns-preview", value_to_set=varformulti
            )
        return self

    def max_count(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Limit the number of matching lines per file searched to NUM."""
        if get_help:
            print(self.helpdict["max_count"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--max-count"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--max-count", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--max-count"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--max-count"] is False and not multi_allowed:
                self.execute_dict["--max-count"] = option
            varformulti = option
        else:
            self.execute_dict["--max-count"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--max-count", value_to_set=varformulti
            )
        return self

    def max_depth(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Limit the depth of directory traversal to NUM levels beyond the paths given. A value of zero only
        searches the explicitly given paths themselves.  For example, 'rg --max-depth 0 dir/' is a no-op
        because dir/ will not be descended into. 'rg --max-depth 1 dir/' will search only the direct
        children of 'dir'."""
        if get_help:
            print(self.helpdict["max_depth"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--max-depth"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--max-depth", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--max-depth"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--max-depth"] is False and not multi_allowed:
                self.execute_dict["--max-depth"] = option
            varformulti = option
        else:
            self.execute_dict["--max-depth"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--max-depth", value_to_set=varformulti
            )
        return self

    def max_filesize(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Ignore files larger than NUM in size. This does not apply to directories.  The input format accepts
        suffixes of K, M or G which correspond to kilobytes, megabytes and gigabytes, respectively. If no
        suffix is provided the input is treated as bytes.  Examples: --max-filesize 50K or --max-filesize
        80M"""
        if get_help:
            print(self.helpdict["max_filesize"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--max-filesize"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--max-filesize", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--max-filesize"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--max-filesize"] is False and not multi_allowed:
                self.execute_dict["--max-filesize"] = option
            varformulti = option
        else:
            self.execute_dict["--max-filesize"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--max-filesize", value_to_set=varformulti
            )
        return self

    def mmap(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Search using memory maps when possible. This is enabled by default when ripgrep thinks it will be
        faster.  Memory map searching doesn't currently support all options, so if an incompatible option
        (e.g., --context) is given with --mmap, then memory maps will not be used.  Note that ripgrep may
        abort unexpectedly when --mmap if it searches a file that is simultaneously truncated.  This flag
        overrides --no-mmap."""
        if get_help:
            print(self.helpdict["mmap"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--mmap"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--mmap", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--mmap"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--mmap"] is False and not multi_allowed:
                self.execute_dict["--mmap"] = option
            varformulti = option
        else:
            self.execute_dict["--mmap"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--mmap", value_to_set=varformulti
            )
        return self

    def multiline(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Enable matching across multiple lines.  When multiline mode is enabled, ripgrep will lift the
        restriction that a match cannot include a line terminator. For example, when multiline mode is not
        enabled (the default), then the regex '\p{any}' will match any Unicode codepoint other than '.
        Similarly, the regex ' is explicitly forbidden, and if you try to use it, ripgrep will return an
        error. However, when multiline mode is enabled, '\p{any}' will match any Unicode codepoint,
        including ', and regexes like ' are permitted.  An important caveat is that multiline mode does
        not change the match semantics of '.'. Namely, in most regex matchers, a '.' will by default match
        any character other than ', and this is true in ripgrep as well. In order to make '.' match ', you
        must enable the "dot all" flag inside the regex. For example, both '(?s).' and '(?s:.)' have the
        same semantics, where '.' will match any character, including '. Alternatively, the '--multiline-
        dotall' flag may be passed to make the "dot all" behavior the default. This flag only applies when
        multiline search is enabled.  There is no limit on the number of the lines that a single match can
        span.  **WARNING**: Because of how the underlying regex engine works, multiline searches may be
        slower than normal line-oriented searches, and they may also use more memory. In particular, when
        multiline mode is enabled, ripgrep requires that each file it searches is laid out contiguously in
        memory (either by reading it onto the heap or by memory-mapping it). Things that cannot be memory-
        mapped (such as stdin) will be consumed until EOF before searching can begin. In general, ripgrep
        will only do these things when necessary. Specifically, if the --multiline flag is provided but the
        regex does not contain patterns that would match ' characters, then ripgrep will automatically
        avoid reading each file into memory before searching it. Nevertheless, if you only care about
        matches spanning at most one line, then it is always better to disable multiline mode.  This flag
        can be disabled with --no-multiline."""
        if get_help:
            print(self.helpdict["multiline"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--multiline"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--multiline", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--multiline"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--multiline"] is False and not multi_allowed:
                self.execute_dict["--multiline"] = option
            varformulti = option
        else:
            self.execute_dict["--multiline"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--multiline", value_to_set=varformulti
            )
        return self

    def multiline_dotall(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """This flag enables "dot all" in your regex pattern, which causes '.' to match newlines when
        multiline searching is enabled. This flag has no effect if multiline searching isn't enabled with
        the --multiline flag.  Normally, a '.' will match any character except newlines. While this behavior
        typically isn't relevant for line-oriented matching (since matches can span at most one line), this
        can be useful when searching with the -U/--multiline flag. By default, the multiline mode runs
        without this flag.  This flag is generally intended to be used in an alias or your ripgrep config
        file if you prefer "dot all" semantics by default. Note that regardless of whether this flag is
        used, "dot all" semantics can still be controlled via inline flags in the regex pattern itself,
        e.g., '(?s:.)' always enables "dot all" whereas '(?-s:.)' always disables "dot all".  This flag can
        be disabled with --no-multiline-dotall."""
        if get_help:
            print(self.helpdict["multiline_dotall"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--multiline-dotall"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--multiline-dotall", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--multiline-dotall"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--multiline-dotall"] is False and not multi_allowed:
                self.execute_dict["--multiline-dotall"] = option
            varformulti = option
        else:
            self.execute_dict["--multiline-dotall"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--multiline-dotall", value_to_set=varformulti
            )
        return self

    def no_config(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Never read configuration files. When this flag is present, ripgrep will not respect the
        RIPGREP_CONFIG_PATH environment search_in.  If ripgrep ever grows a feature to automatically read
        configuration files in pre-defined locations, then this flag will also disable that behavior as
        well."""
        if get_help:
            print(self.helpdict["no_config"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--no-config"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--no-config", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--no-config"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--no-config"] is False and not multi_allowed:
                self.execute_dict["--no-config"] = option
            varformulti = option
        else:
            self.execute_dict["--no-config"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--no-config", value_to_set=varformulti
            )
        return self

    def no_filename(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Never print the file path with the matched lines. This is the default when ripgrep is explicitly
        instructed to search one file or stdin.  This flag overrides --with-filename."""
        if get_help:
            print(self.helpdict["no_filename"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--no-filename"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--no-filename", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--no-filename"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--no-filename"] is False and not multi_allowed:
                self.execute_dict["--no-filename"] = option
            varformulti = option
        else:
            self.execute_dict["--no-filename"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--no-filename", value_to_set=varformulti
            )
        return self

    def no_heading(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Don't group matches by each file. If --no-heading is provided in addition to the -H/--with-filename
        flag, then file paths will be printed as a prefix for every matched line. This is the default mode
        when not printing to a terminal.  This overrides the --heading flag."""
        if get_help:
            print(self.helpdict["no_heading"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--no-heading"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--no-heading", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--no-heading"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--no-heading"] is False and not multi_allowed:
                self.execute_dict["--no-heading"] = option
            varformulti = option
        else:
            self.execute_dict["--no-heading"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--no-heading", value_to_set=varformulti
            )
        return self

    def no_ignore(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Don't respect ignore files (.gitignore, .ignore, etc.). This implies no-ignore-dot, --no-ignore-
        exclude, --no-ignore-global, no-ignore-parent and no-ignore-vcs.  This does *not* imply --no-ignore-
        files, since --ignore-file is specified explicitly as a command line argument.  When given only
        once, the -u flag is identical in behavior to --no-ignore and can be considered an alias. However,
        subsequent -u flags have additional effects; see --unrestricted.  This flag can be disabled with the
        --ignore flag."""
        if get_help:
            print(self.helpdict["no_ignore"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--no-ignore"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--no-ignore", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--no-ignore"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--no-ignore"] is False and not multi_allowed:
                self.execute_dict["--no-ignore"] = option
            varformulti = option
        else:
            self.execute_dict["--no-ignore"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--no-ignore", value_to_set=varformulti
            )
        return self

    def no_ignore_dot(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Don't respect .ignore files.  This does *not* affect whether ripgrep will ignore files and
        directories whose names begin with a dot. For that, see the -./--hidden flag.  This flag can be
        disabled with the --ignore-dot flag."""
        if get_help:
            print(self.helpdict["no_ignore_dot"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--no-ignore-dot"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--no-ignore-dot", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--no-ignore-dot"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--no-ignore-dot"] is False and not multi_allowed:
                self.execute_dict["--no-ignore-dot"] = option
            varformulti = option
        else:
            self.execute_dict["--no-ignore-dot"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--no-ignore-dot", value_to_set=varformulti
            )
        return self

    def no_ignore_exclude(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Don't respect ignore files that are manually configured for the repository such as git's
        '.git/info/exclude'.  This flag can be disabled with the --ignore-exclude flag."""
        if get_help:
            print(self.helpdict["no_ignore_exclude"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--no-ignore-exclude"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--no-ignore-exclude", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--no-ignore-exclude"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--no-ignore-exclude"] is False and not multi_allowed:
                self.execute_dict["--no-ignore-exclude"] = option
            varformulti = option
        else:
            self.execute_dict["--no-ignore-exclude"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--no-ignore-exclude", value_to_set=varformulti
            )
        return self

    def no_ignore_files(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """When set, any --ignore-file flags, even ones that come after this flag, are ignored.  This flag can
        be disabled with the --ignore-files flag."""
        if get_help:
            print(self.helpdict["no_ignore_files"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--no-ignore-files"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--no-ignore-files", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--no-ignore-files"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--no-ignore-files"] is False and not multi_allowed:
                self.execute_dict["--no-ignore-files"] = option
            varformulti = option
        else:
            self.execute_dict["--no-ignore-files"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--no-ignore-files", value_to_set=varformulti
            )
        return self

    def no_ignore_global(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Don't respect ignore files that come from "global" sources such as git's `core.excludesFile`
        configuration option (which defaults to `$HOME/.config/git/ignore`).  This flag can be disabled with
        the --ignore-global flag."""
        if get_help:
            print(self.helpdict["no_ignore_global"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--no-ignore-global"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--no-ignore-global", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--no-ignore-global"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--no-ignore-global"] is False and not multi_allowed:
                self.execute_dict["--no-ignore-global"] = option
            varformulti = option
        else:
            self.execute_dict["--no-ignore-global"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--no-ignore-global", value_to_set=varformulti
            )
        return self

    def no_ignore_messages(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Suppresses all error messages related to parsing ignore files such as .ignore or .gitignore.  This
        flag can be disabled with the --ignore-messages flag."""
        if get_help:
            print(self.helpdict["no_ignore_messages"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--no-ignore-messages"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--no-ignore-messages", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--no-ignore-messages"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--no-ignore-messages"] is False and not multi_allowed:
                self.execute_dict["--no-ignore-messages"] = option
            varformulti = option
        else:
            self.execute_dict["--no-ignore-messages"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--no-ignore-messages", value_to_set=varformulti
            )
        return self

    def no_ignore_parent(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Don't respect ignore files (.gitignore, .ignore, etc.) in parent directories.  This flag can be
        disabled with the --ignore-parent flag."""
        if get_help:
            print(self.helpdict["no_ignore_parent"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--no-ignore-parent"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--no-ignore-parent", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--no-ignore-parent"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--no-ignore-parent"] is False and not multi_allowed:
                self.execute_dict["--no-ignore-parent"] = option
            varformulti = option
        else:
            self.execute_dict["--no-ignore-parent"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--no-ignore-parent", value_to_set=varformulti
            )
        return self

    def no_ignore_vcs(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Don't respect version control ignore files (.gitignore, etc.). This implies no-ignore-parent for
        VCS files. Note that .ignore files will continue to be respected.  This flag can be disabled with
        the --ignore-vcs flag."""
        if get_help:
            print(self.helpdict["no_ignore_vcs"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--no-ignore-vcs"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--no-ignore-vcs", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--no-ignore-vcs"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--no-ignore-vcs"] is False and not multi_allowed:
                self.execute_dict["--no-ignore-vcs"] = option
            varformulti = option
        else:
            self.execute_dict["--no-ignore-vcs"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--no-ignore-vcs", value_to_set=varformulti
            )
        return self

    def no_line_number(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Suppress line numbers. This is enabled by default when not searching in a terminal."""
        if get_help:
            print(self.helpdict["no_line_number"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--no-line-number"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--no-line-number", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--no-line-number"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--no-line-number"] is False and not multi_allowed:
                self.execute_dict["--no-line-number"] = option
            varformulti = option
        else:
            self.execute_dict["--no-line-number"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--no-line-number", value_to_set=varformulti
            )
        return self

    def no_messages(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Suppress all error messages related to opening and reading files. Error messages related to the
        syntax of the pattern given are still shown.  This flag can be disabled with the --messages flag."""
        if get_help:
            print(self.helpdict["no_messages"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--no-messages"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--no-messages", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--no-messages"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--no-messages"] is False and not multi_allowed:
                self.execute_dict["--no-messages"] = option
            varformulti = option
        else:
            self.execute_dict["--no-messages"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--no-messages", value_to_set=varformulti
            )
        return self

    def no_mmap(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Never use memory maps, even when they might be faster.  This flag overrides --mmap."""
        if get_help:
            print(self.helpdict["no_mmap"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--no-mmap"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--no-mmap", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--no-mmap"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--no-mmap"] is False and not multi_allowed:
                self.execute_dict["--no-mmap"] = option
            varformulti = option
        else:
            self.execute_dict["--no-mmap"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--no-mmap", value_to_set=varformulti
            )
        return self

    def no_pcre2_unicode(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """DEPRECATED. Use --no-unicode instead.  This flag is now an alias for --no-unicode. And
        --pcre2-unicode is an alias for --unicode."""
        if get_help:
            print(self.helpdict["no_pcre2_unicode"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--no-pcre2-unicode"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--no-pcre2-unicode", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--no-pcre2-unicode"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--no-pcre2-unicode"] is False and not multi_allowed:
                self.execute_dict["--no-pcre2-unicode"] = option
            varformulti = option
        else:
            self.execute_dict["--no-pcre2-unicode"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--no-pcre2-unicode", value_to_set=varformulti
            )
        return self

    def no_require_git(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """By default, ripgrep will only respect global gitignore rules, .gitignore rules and local exclude
        rules if ripgrep detects that you are searching inside a git repository. This flag allows you to
        relax this restriction such that ripgrep will respect all git related ignore rules regardless of
        whether you're searching in a git repository or not.  This flag can be disabled with --require-git."""
        if get_help:
            print(self.helpdict["no_require_git"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--no-require-git"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--no-require-git", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--no-require-git"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--no-require-git"] is False and not multi_allowed:
                self.execute_dict["--no-require-git"] = option
            varformulti = option
        else:
            self.execute_dict["--no-require-git"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--no-require-git", value_to_set=varformulti
            )
        return self

    def no_unicode(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """By default, ripgrep will enable "Unicode mode" in all of its regexes. This has a number of
        consequences:  * '.' will only match valid UTF-8 encoded scalar values. * Classes like '\w', '\s',
        '\d' are all Unicode aware and much bigger than their ASCII only versions. * Case insensitive
        matching will use Unicode case folding. * A large array of classes like '\p{Emoji}' are available. *
        Word boundaries (' and '\B') use the Unicode definition of a word character.  In some cases it can
        be desirable to turn these things off. The --no-unicode flag will do exactly that.  For PCRE2
        specifically, Unicode mode represents a critical trade off in the user experience of ripgrep. In
        particular, unlike the default regex engine, PCRE2 does not support the ability to search possibly
        invalid UTF-8 with Unicode features enabled. Instead, PCRE2 *requires* that everything it searches
        when Unicode mode is enabled is valid UTF-8. (Or valid UTF-16/UTF-32, but for the purposes of
        ripgrep, we only discuss UTF-8.) This means that if you have PCRE2's Unicode mode enabled and you
        attempt to search invalid UTF-8, then the search for that file will halt and print an error. For
        this reason, when PCRE2's Unicode mode is enabled, ripgrep will automatically "fix" invalid UTF-8
        sequences by replacing them with the Unicode replacement codepoint. This penalty does not occur when
        using the default regex engine.  If you would rather see the encoding errors surfaced by PCRE2 when
        Unicode mode is enabled, then pass the --no-encoding flag to disable all transcoding.  The --no-
        unicode flag can be disabled with --unicode. Note that no-pcre2-unicode and --pcre2-unicode are
        aliases for --no-unicode and unicode, respectively."""
        if get_help:
            print(self.helpdict["no_unicode"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--no-unicode"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--no-unicode", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--no-unicode"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--no-unicode"] is False and not multi_allowed:
                self.execute_dict["--no-unicode"] = option
            varformulti = option
        else:
            self.execute_dict["--no-unicode"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--no-unicode", value_to_set=varformulti
            )
        return self

    def null(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Whenever a file path is printed, follow it with a NUL byte. This includes printing file paths
        before matches, and when printing a list of matching files such as with --count, --files-with-
        matches and --files. This option is useful for use with xargs."""
        if get_help:
            print(self.helpdict["null"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--null"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--null", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--null"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--null"] is False and not multi_allowed:
                self.execute_dict["--null"] = option
            varformulti = option
        else:
            self.execute_dict["--null"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--null", value_to_set=varformulti
            )
        return self

    def null_data(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Enabling this option causes ripgrep to use NUL as a line terminator instead of the default of '.
        This is useful when searching large binary files that would otherwise have very long lines if '
        were used as the line terminator. In particular, ripgrep requires that, at a minimum, each line must
        fit into memory. Using NUL instead can be a useful stopgap to keep memory requirements low and avoid
        OOM (out of memory) conditions.  This is also useful for processing NUL delimited data, such as that
        emitted when using ripgrep's -0/--null flag or find's --print0 flag.  Using this flag implies
        -a/--text."""
        if get_help:
            print(self.helpdict["null_data"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--null-data"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--null-data", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--null-data"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--null-data"] is False and not multi_allowed:
                self.execute_dict["--null-data"] = option
            varformulti = option
        else:
            self.execute_dict["--null-data"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--null-data", value_to_set=varformulti
            )
        return self

    def one_file_system(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """When enabled, ripgrep will not cross file system boundaries relative to where the search started
        from.  Note that this applies to each path argument given to ripgrep. For example, in the command
        'rg --one-file-system /foo/bar /quux/baz', ripgrep will search both '/foo/bar' and '/quux/baz' even
        if they are on different file systems, but will not cross a file system boundary when traversing
        each path's directory tree.  This is similar to find's '-xdev' or '-mount' flag.  This flag can be
        disabled with --no-one-file-system."""
        if get_help:
            print(self.helpdict["one_file_system"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--one-file-system"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--one-file-system", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--one-file-system"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--one-file-system"] is False and not multi_allowed:
                self.execute_dict["--one-file-system"] = option
            varformulti = option
        else:
            self.execute_dict["--one-file-system"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--one-file-system", value_to_set=varformulti
            )
        return self

    def only_matching(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Print only the matched (non-empty) parts of a matching line, with each such part on a separate
        output line."""
        if get_help:
            print(self.helpdict["only_matching"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--only-matching"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--only-matching", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--only-matching"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--only-matching"] is False and not multi_allowed:
                self.execute_dict["--only-matching"] = option
            varformulti = option
        else:
            self.execute_dict["--only-matching"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--only-matching", value_to_set=varformulti
            )
        return self

    def passthru(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Print both matching and non-matching lines.  Another way to achieve a similar effect is by
        modifying your pattern to match the empty string. For example, if you are searching using 'rg foo'
        then using 'rg "^|foo"' instead will emit every line in every file searched, but only occurrences of
        'foo' will be highlighted. This flag enables the same behavior without needing to modify the
        pattern.  This overrides the --context, --after-context and --before-context flags."""
        if get_help:
            print(self.helpdict["passthru"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--passthru"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--passthru", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--passthru"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--passthru"] is False and not multi_allowed:
                self.execute_dict["--passthru"] = option
            varformulti = option
        else:
            self.execute_dict["--passthru"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--passthru", value_to_set=varformulti
            )
        return self

    def path_separator(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Set the path separator to use when printing file paths. This defaults to your platform's path
        separator, which is / on Unix and \ on Windows. This flag is intended for overriding the default
        when the environment demands it (e.g., cygwin). A path separator is limited to a single byte."""
        if get_help:
            print(self.helpdict["path_separator"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--path-separator"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--path-separator", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--path-separator"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--path-separator"] is False and not multi_allowed:
                self.execute_dict["--path-separator"] = option
            varformulti = option
        else:
            self.execute_dict["--path-separator"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--path-separator", value_to_set=varformulti
            )
        return self

    def pcre2(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """When this flag is present, ripgrep will use the PCRE2 regex engine instead of its default regex
        engine.  This is generally useful when you want to use features such as look-around or
        backreferences.  Note that PCRE2 is an optional ripgrep feature. If PCRE2 wasn't included in your
        build of ripgrep, then using this flag will result in ripgrep printing an error message and exiting.
        PCRE2 may also have worse user experience in some cases, since it has fewer introspection APIs than
        ripgrep's default regex engine. For example, if you use a ' in a PCRE2 regex without the
        '-U/--multiline' flag, then ripgrep will silently fail to match anything instead of reporting an
        error immediately (like it does with the default regex engine).  Related flags: --no-pcre2-unicode
        This flag can be disabled with --no-pcre2."""
        if get_help:
            print(self.helpdict["pcre2"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--pcre2"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--pcre2", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--pcre2"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--pcre2"] is False and not multi_allowed:
                self.execute_dict["--pcre2"] = option
            varformulti = option
        else:
            self.execute_dict["--pcre2"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--pcre2", value_to_set=varformulti
            )
        return self

    def pcre2_version(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """When this flag is present, ripgrep will print the version of PCRE2 in use, along with other
        information, and then exit. If PCRE2 is not available, then ripgrep will print an error message and
        exit with an error code."""
        if get_help:
            print(self.helpdict["pcre2_version"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--pcre2-version"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--pcre2-version", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--pcre2-version"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--pcre2-version"] is False and not multi_allowed:
                self.execute_dict["--pcre2-version"] = option
            varformulti = option
        else:
            self.execute_dict["--pcre2-version"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--pcre2-version", value_to_set=varformulti
            )
        return self

    def pre(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """For each input FILE, search the standard output of COMMAND FILE rather than the contents of FILE.
        This option expects the COMMAND program to either be an absolute path or to be available in your
        PATH. Either an empty string COMMAND or the '--no-pre' flag will disable this behavior.  WARNING:
        When this flag is set, ripgrep will unconditionally spawn a process for every file that is searched.
        Therefore, this can incur an unnecessarily large performance penalty if you don't otherwise need the
        flexibility offered by this flag. One possible mitigation to this is to use the '--pre-glob' flag to
        limit which files a preprocessor is run with.  A preprocessor is not run when ripgrep is searching
        stdin.  When searching over sets of files that may require one of several decoders as preprocessors,
        COMMAND should be a wrapper program or script which first classifies FILE based on magic
        numbers/content or based on the FILE name and then dispatches to an appropriate preprocessor. Each
        COMMAND also has its standard input connected to FILE for convenience.  For example, a shell script
        for COMMAND might look like:  case "$1" in *.pdf) exec pdftotext "$1" - ;; *) case $(file "$1") in
        *Zstandard*) exec pzstd -cdq ;; *) exec cat ;; esac ;; esac  The above script uses `pdftotext` to
        convert a PDF file to plain text. For all other files, the script uses the `file` utility to sniff
        the type of the file based on its contents. If it is a compressed file in the Zstandard format, then
        `pzstd` is used to decompress the contents to stdout.  This overrides the -z/--search-zip flag."""
        if get_help:
            print(self.helpdict["pre"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--pre"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--pre", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--pre"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--pre"] is False and not multi_allowed:
                self.execute_dict["--pre"] = option
            varformulti = option
        else:
            self.execute_dict["--pre"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--pre", value_to_set=varformulti
            )
        return self

    def pretty(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """This is a convenience alias for '--color always --heading --line-number'. This flag is useful when
        you still want pretty output even if you're piping ripgrep to another program or file. For example:
        'rg -p foo | less -R'."""
        if get_help:
            print(self.helpdict["pretty"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--pretty"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--pretty", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--pretty"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--pretty"] is False and not multi_allowed:
                self.execute_dict["--pretty"] = option
            varformulti = option
        else:
            self.execute_dict["--pretty"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--pretty", value_to_set=varformulti
            )
        return self

    def quiet(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Do not print anything to stdout. If a match is found in a file, then ripgrep will stop searching.
        This is useful when ripgrep is used only for its exit code (which will be an error if no matches are
        found).  When --files is used, then ripgrep will stop finding files after finding the first file
        that matches all ignore rules."""
        if get_help:
            print(self.helpdict["quiet"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--quiet"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--quiet", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--quiet"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--quiet"] is False and not multi_allowed:
                self.execute_dict["--quiet"] = option
            varformulti = option
        else:
            self.execute_dict["--quiet"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--quiet", value_to_set=varformulti
            )
        return self

    def regex_size_limit(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """The upper size limit of the compiled regex. The default limit is 10M.  The argument accepts the
        same size suffixes as allowed in the --max-filesize flag."""
        if get_help:
            print(self.helpdict["regex_size_limit"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--regex-size-limit"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--regex-size-limit", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--regex-size-limit"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--regex-size-limit"] is False and not multi_allowed:
                self.execute_dict["--regex-size-limit"] = option
            varformulti = option
        else:
            self.execute_dict["--regex-size-limit"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--regex-size-limit", value_to_set=varformulti
            )
        return self

    def regexp(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """A pattern to search for. This option can be provided multiple times, where all patterns given are
        searched. Lines matching at least one of the provided patterns are printed. This flag can also be
        used when searching for patterns that start with a dash.  For example, to search for the literal
        '-foo', you can use this flag:  rg -e -foo  You can also use the special '--' delimiter to indicate
        that no more flags will be provided. Namely, the following is equivalent to the above:  rg -- -foo"""
        if get_help:
            print(self.helpdict["regexp"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--regexp"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--regexp", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--regexp"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--regexp"] is False and not multi_allowed:
                self.execute_dict["--regexp"] = option
            varformulti = option
        else:
            self.execute_dict["--regexp"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--regexp", value_to_set=varformulti
            )
        return self

    def replace(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Replace every match with the text given when printing results. Neither this flag nor any other
        ripgrep flag will modify your files.  Capture group indices (e.g., $5) and names (e.g., $foo) are
        supported in the replacement string. Capture group indices are numbered based on the position of the
        opening parenthesis of the group, where the leftmost such group is $1. The special $0 group
        corresponds to the entire match.  In shells such as Bash and zsh, you should wrap the pattern in
        single quotes instead of double quotes. Otherwise, capture group indices will be replaced by
        expanded shell variables which will most likely be empty.  To write a literal '$', use '$$'.  Note
        that the replacement by default replaces each match, and NOT the entire line. To replace the entire
        line, you should match the entire line.  This flag can be used with the -o/--only-matching flag."""
        if get_help:
            print(self.helpdict["replace"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--replace"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--replace", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--replace"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--replace"] is False and not multi_allowed:
                self.execute_dict["--replace"] = option
            varformulti = option
        else:
            self.execute_dict["--replace"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--replace", value_to_set=varformulti
            )
        return self

    def search_zip(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Search in compressed files. Currently gzip, bzip2, xz, LZ4, LZMA, Brotli and Zstd files are
        supported. This option expects the decompression binaries to be available in your PATH.  This flag
        can be disabled with --no-search-zip."""
        if get_help:
            print(self.helpdict["search_zip"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--search-zip"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--search-zip", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--search-zip"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--search-zip"] is False and not multi_allowed:
                self.execute_dict["--search-zip"] = option
            varformulti = option
        else:
            self.execute_dict["--search-zip"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--search-zip", value_to_set=varformulti
            )
        return self

    def smart_case(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Searches case insensitively if the pattern is all lowercase. Search case sensitively otherwise.  A
        pattern is considered all lowercase if both of the following rules hold:  First, the pattern
        contains at least one literal character. For example, 'a\w' contains a literal ('a') but just '\w'
        does not.  Second, of the literals in the pattern, none of them are considered to be uppercase
        according to Unicode. For example, 'foo\pL' has no uppercase literals but 'Foo\pL' does.  This
        overrides the -s/--case-sensitive and -i/--ignore-case flags."""
        if get_help:
            print(self.helpdict["smart_case"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--smart-case"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--smart-case", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--smart-case"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--smart-case"] is False and not multi_allowed:
                self.execute_dict["--smart-case"] = option
            varformulti = option
        else:
            self.execute_dict["--smart-case"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--smart-case", value_to_set=varformulti
            )
        return self

    def sort(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """This flag enables sorting of results in ascending order. The possible values for this flag are:
        none      (Default) Do not sort results. Fastest. Can be multi-threaded. path      Sort by file
        path. Always single-threaded. modified  Sort by the last modified time on a file. Always single-
        threaded. accessed  Sort by the last accessed time on a file. Always single-threaded. created   Sort
        by the creation time on a file. Always single-threaded.  If the chosen (manually or by-default)
        sorting criteria isn't available on your system (for example, creation time is not available on ext4
        file systems), then ripgrep will attempt to detect this, print an error and exit without searching.
        To sort results in reverse or descending order, use the --sortr flag. Also, this flag overrides
        --sortr.  Note that sorting results currently always forces ripgrep to abandon parallelism and run
        in a single thread."""
        if get_help:
            print(self.helpdict["sort"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--sort"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--sort", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--sort"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--sort"] is False and not multi_allowed:
                self.execute_dict["--sort"] = option
            varformulti = option
        else:
            self.execute_dict["--sort"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--sort", value_to_set=varformulti
            )
        return self

    def sortr(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """This flag enables sorting of results in descending order. The possible values for this flag are:
        none      (Default) Do not sort results. Fastest. Can be multi-threaded. path      Sort by file
        path. Always single-threaded. modified  Sort by the last modified time on a file. Always single-
        threaded. accessed  Sort by the last accessed time on a file. Always single-threaded. created   Sort
        by the creation time on a file. Always single-threaded.  If the chosen (manually or by-default)
        sorting criteria isn't available on your system (for example, creation time is not available on ext4
        file systems), then ripgrep will attempt to detect this, print an error and exit without searching.
        To sort results in ascending order, use the --sort flag. Also, this flag overrides --sort.  Note
        that sorting results currently always forces ripgrep to abandon parallelism and run in a single
        thread."""
        if get_help:
            print(self.helpdict["sortr"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--sortr"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--sortr", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--sortr"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--sortr"] is False and not multi_allowed:
                self.execute_dict["--sortr"] = option
            varformulti = option
        else:
            self.execute_dict["--sortr"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--sortr", value_to_set=varformulti
            )
        return self

    def stats(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Print aggregate statistics about this ripgrep search. When this flag is present, ripgrep will print
        the following stats to stdout at the end of the search: number of matched lines, number of files
        with matches, number of files searched, and the time taken for the entire search to complete.  This
        set of aggregate statistics may expand over time.  Note that this flag has no effect if --files,
        --files-with-matches or files-without-match is passed.  This flag can be disabled with --no-stats."""
        if get_help:
            print(self.helpdict["stats"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--stats"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--stats", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--stats"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--stats"] is False and not multi_allowed:
                self.execute_dict["--stats"] = option
            varformulti = option
        else:
            self.execute_dict["--stats"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--stats", value_to_set=varformulti
            )
        return self

    def text(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Search binary files as if they were text. When this flag is present, ripgrep's binary file
        detection is disabled. This means that when a binary file is searched, its contents may be printed
        if there is a match. This may cause escape codes to be printed that alter the behavior of your
        terminal.  When binary file detection is enabled it is imperfect. In general, it uses a simple
        heuristic. If a NUL byte is seen during search, then the file is considered binary and search stops
        (unless this flag is present). Alternatively, if the '--binary' flag is used, then ripgrep will only
        quit when it sees a NUL byte after it sees a match (or searches the entire file).  This flag can be
        disabled with '--no-text'. It overrides the '--binary' flag."""
        if get_help:
            print(self.helpdict["text"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--text"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--text", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--text"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--text"] is False and not multi_allowed:
                self.execute_dict["--text"] = option
            varformulti = option
        else:
            self.execute_dict["--text"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--text", value_to_set=varformulti
            )
        return self

    def threads(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """The approximate number of threads to use. A value of 0 (which is the default) causes ripgrep to
        choose the thread count using heuristics."""
        if get_help:
            print(self.helpdict["threads"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--threads"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--threads", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--threads"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--threads"] is False and not multi_allowed:
                self.execute_dict["--threads"] = option
            varformulti = option
        else:
            self.execute_dict["--threads"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--threads", value_to_set=varformulti
            )
        return self

    def trim(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """When set, all ASCII whitespace at the beginning of each line printed will be trimmed.  This flag
        can be disabled with --no-trim."""
        if get_help:
            print(self.helpdict["trim"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--trim"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--trim", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--trim"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--trim"] is False and not multi_allowed:
                self.execute_dict["--trim"] = option
            varformulti = option
        else:
            self.execute_dict["--trim"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--trim", value_to_set=varformulti
            )
        return self

    def type(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Only search files matching TYPE. Multiple type flags may be provided. Use the type-list flag to
        list all available types.  This flag supports the special value 'all', which will behave as if
        --type was provided for every file type supported by ripgrep (including any custom file types). The
        end result is that '--type all' causes ripgrep to search in "whitelist" mode, where it will only
        search files it recognizes via its type definitions."""
        if get_help:
            print(self.helpdict["type"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--type"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--type", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--type"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--type"] is False and not multi_allowed:
                self.execute_dict["--type"] = option
            varformulti = option
        else:
            self.execute_dict["--type"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--type", value_to_set=varformulti
            )
        return self

    def type_add(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Add a new glob for a particular file type. Only one glob can be added at a time. Multiple --type-
        add flags can be provided. Unless --type-clear is used, globs are added to any existing globs
        defined inside of ripgrep.  Note that this MUST be passed to every invocation of ripgrep. Type
        settings are NOT persisted. See CONFIGURATION FILES for a workaround.  Example:  rg --type-add
        'foo:*.foo' -tfoo PATTERN.  type-add can also be used to include rules from other types with the
        special include directive. The include directive permits specifying one or more other type names
        (separated by a comma) that have been defined and its rules will automatically be imported into the
        type specified. For example, to create a type called src that matches C++, Python and Markdown
        files, one can use:  type-add 'src:include:cpp,py,md'  Additional glob rules can still be added to
        the src type by using the type-add flag again:  type-add 'src:include:cpp,py,md' --type-add
        'src:*.foo'  Note that type names must consist only of Unicode letters or numbers. Punctuation
        characters are not allowed."""
        if get_help:
            print(self.helpdict["type_add"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--type-add"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--type-add", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--type-add"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--type-add"] is False and not multi_allowed:
                self.execute_dict["--type-add"] = option
            varformulti = option
        else:
            self.execute_dict["--type-add"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--type-add", value_to_set=varformulti
            )
        return self

    def type_clear(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """... Clear the file type globs previously defined for TYPE. This only clears the default type
        definitions that are found inside of ripgrep.  Note that this MUST be passed to every invocation of
        ripgrep. Type settings are NOT persisted. See CONFIGURATION FILES for a workaround."""
        if get_help:
            print(self.helpdict["type_clear"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--type-clear"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--type-clear", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--type-clear"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--type-clear"] is False and not multi_allowed:
                self.execute_dict["--type-clear"] = option
            varformulti = option
        else:
            self.execute_dict["--type-clear"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--type-clear", value_to_set=varformulti
            )
        return self

    def type_list(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Show all supported file types and their corresponding globs."""
        if get_help:
            print(self.helpdict["type_list"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--type-list"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--type-list", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--type-list"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--type-list"] is False and not multi_allowed:
                self.execute_dict["--type-list"] = option
            varformulti = option
        else:
            self.execute_dict["--type-list"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--type-list", value_to_set=varformulti
            )
        return self

    def type_not(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """... Do not search files matching TYPE. Multiple type-not flags may be provided. Use the --type-
        list flag to list all available types."""
        if get_help:
            print(self.helpdict["type_not"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--type-not"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--type-not", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--type-not"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--type-not"] is False and not multi_allowed:
                self.execute_dict["--type-not"] = option
            varformulti = option
        else:
            self.execute_dict["--type-not"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--type-not", value_to_set=varformulti
            )
        return self

    def unrestricted(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Reduce the level of "smart" searching. A single -u won't respect .gitignore (etc.) files (--no-
        ignore). Two -u flags will additionally search hidden files and directories (-./--hidden). Three -u
        flags will additionally search binary files (--binary).  'rg -uuu' is roughly equivalent to 'grep
        -r'."""
        if get_help:
            print(self.helpdict["unrestricted"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--unrestricted"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--unrestricted", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--unrestricted"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--unrestricted"] is False and not multi_allowed:
                self.execute_dict["--unrestricted"] = option
            varformulti = option
        else:
            self.execute_dict["--unrestricted"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--unrestricted", value_to_set=varformulti
            )
        return self

    def version(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Prints version information"""
        if get_help:
            print(self.helpdict["version"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--version"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--version", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--version"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--version"] is False and not multi_allowed:
                self.execute_dict["--version"] = option
            varformulti = option
        else:
            self.execute_dict["--version"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--version", value_to_set=varformulti
            )
        return self

    def vimgrep(self, option=None, activated=True, multi_allowed=False, get_help=False):
        """Show results with every match on its own line, including line numbers and column numbers. With this
        option, a line with more than one match will be printed more than once."""
        if get_help:
            print(self.helpdict["vimgrep"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--vimgrep"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--vimgrep", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--vimgrep"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--vimgrep"] is False and not multi_allowed:
                self.execute_dict["--vimgrep"] = option
            varformulti = option
        else:
            self.execute_dict["--vimgrep"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--vimgrep", value_to_set=varformulti
            )
        return self

    def with_filename(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Display the file path for matches. This is the default when more than one file is searched. If
        --heading is enabled (the default when printing to a terminal), the file path will be shown above
        clusters of matches from each file; otherwise, the file name will be shown as a prefix for each
        matched line.  This flag overrides --no-filename."""
        if get_help:
            print(self.helpdict["with_filename"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--with-filename"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--with-filename", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--with-filename"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--with-filename"] is False and not multi_allowed:
                self.execute_dict["--with-filename"] = option
            varformulti = option
        else:
            self.execute_dict["--with-filename"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--with-filename", value_to_set=varformulti
            )
        return self

    def word_regexp(
        self, option=None, activated=True, multi_allowed=False, get_help=False
    ):
        """Only show matches surrounded by word boundaries. This is roughly equivalent to putting before and
        after all of the search patterns.  This overrides the --line-regexp flag."""
        if get_help:
            print(self.helpdict["word_regexp"])
            return self
        varformulti = ""
        if not activated:
            self.execute_dict["--word-regexp"] = False
            if multi_allowed:
                self._handle_multiple_times_same_flag(
                    key_to_check="--word-regexp", value_to_set=False
                )
            return self
        if isinstance(option, bool):
            self._print_option_activate_warning()
            self.execute_dict["--word-regexp"] = True
            varformulti = True

        elif option is not None and activated:
            if self.execute_dict["--word-regexp"] is False and not multi_allowed:
                self.execute_dict["--word-regexp"] = option
            varformulti = option
        else:
            self.execute_dict["--word-regexp"] = True
            varformulti = True
        if multi_allowed:
            self._handle_multiple_times_same_flag(
                key_to_check="--word-regexp", value_to_set=varformulti
            )
        return self


class RePatterns:
    def __init__(self):
        self.pygrep = PyRipGREP()

    def _convert_std_lst(self, ziptemp, numpy_df_or_gen):
        if numpy_df_or_gen == "df":
            df = pd.DataFrame.from_records(ziptemp)

            df = PDTools(df).aa_pd_horizonal_explode([1])
            df.columns = [
                "aa_filename",
                "aa_line",
                "aa_byte_offset",
                "aa_byte_offset_o",
                "aa_string",
            ]
            df.aa_filename = df.aa_filename.astype("category")
            df.aa_line = df.aa_line.astype("uint32")
            df.aa_byte_offset = df.aa_byte_offset.astype("uint32")
            df.aa_byte_offset_o = df.aa_byte_offset_o.astype("uint32")
            df.aa_string = df.aa_string.astype("string")

        elif numpy_df_or_gen == "gen":
            df = zip(ziptemp)

        else:
            df = np.fromiter(
                [[x[0][0], *x[0][1]] for x in zip(ziptemp)],
                dtype="object",
            )
        return df

    def _return_if_nothing_found(self, outputtype):
        df = None
        if outputtype == "df":
            df = pd.DataFrame(
                columns=[
                    "aa_filename",
                    "aa_line",
                    "aa_byte_offset",
                    "aa_byte_offset_o",
                    "aa_string",
                ]
            )
            df.aa_filename = df.aa_filename.astype("category")
            df.aa_line = df.aa_line.astype("uint32")
            df.aa_byte_offset = df.aa_byte_offset.astype("uint32")
            df.aa_byte_offset_o = df.aa_byte_offset_o.astype("uint32")
            df.aa_string = df.aa_string.astype("string")

        if outputtype == "np":
            df = np.array([], dtype="object")
        if outputtype == "dict":
            df = {}

        if outputtype == "gen":
            pass

        return df

    def _escape_filenames_lst(self, path_to_search):
        if isinstance(path_to_search, str):
            path_to_search = [path_to_search]
        path_to_search = [regex.escape(x) for x in path_to_search]
        path_to_search = r"(?:" + r"|".join(path_to_search) + r")"
        return path_to_search

    def _decode_output_lst(self, result, outputencoding="utf-8"):
        return result.stdout.decode(outputencoding, errors="ignore").strip("\x00")

    def _delete_trash_lst(self, result, filetosearch):
        return (
            x
            for a, x in enumerate(regex.split(f"\\x00?({filetosearch})", result))
            if a != 0 and x != ""
        )

    def _split_field_sep_lst(self, field_match_separator, result):
        return [regex.split(rf"\s*{field_match_separator}\s*", x) for x in result]

    def _get_splt_list(self, result):
        return zip(
            [y[0] for x, y in enumerate(result) if x % 2 == 0],
            [y[1:] for x, y in enumerate(result) if x % 2 != 0],
        )

    def _to_list(self, variable):
        if not isinstance(variable, list):
            variable = [variable]
        return variable

    def _check_key(self, texte):
        good_results = []
        for text in texte:
            if not isinstance(text, dict):
                continue
            if "type" in text:
                if text["type"] in ["end", "begin"]:
                    continue
            if "data" in text:
                if "stats" in text["data"]:
                    continue
            good_results.append(text)
        good_results_final = []

        for finalcheck in good_results:
            finalcheckcopy = finalcheck.copy()
            if "type" in finalcheckcopy.keys():
                del finalcheckcopy["type"]
            if "data" in finalcheckcopy:
                finalcheckcopy = finalcheckcopy["data"]
            good_results_final.append(finalcheckcopy.copy())
        return good_results_final

    def delete_beginning_end_stats(self, text):
        try:
            return ujson.loads(text)
        except Exception as Fe:
            return None

    def _generator_json(self, result, outputencoding):
        return (
            self._check_key(di)
            for di in [
                [
                    self.delete_beginning_end_stats(
                        regex.sub(
                            r'\{"type":"begin"[^\}]+\}\}\}', """\"end\": 1}]}}""", va
                        )
                    )
                    for va in spli.stdout.decode(
                        outputencoding, errors="ignore"
                    ).splitlines()
                ]
                for spli in result
            ]
        )

    def _format_json_dataframe(self, finalresult):
        df4 = finalresult
        datenfraexxa2 = [
            pd.DataFrame(
                [
                    list(y[-1].items())[-1] if y[0] in ["path", "lines"] else y
                    for y in x[0].items()
                ]
            ).T
            for x in df4
        ]
        finaldf = pd.concat([x[1:] for x in datenfraexxa2], ignore_index=True, axis=0)
        finaldf.columns = [
            "path",
            "lines",
            "line_number",
            "absolut_offset",
            "submatches",
        ]
        finaldf = finaldf.explode("submatches")
        finaldf["submatches"] = finaldf.submatches.apply(lambda x: list(x.items()))
        ndf = PDTools(finaldf).aa_pd_horizonal_explode(["submatches"])
        toexplode = [x for x in ndf.columns if regex.findall(r"\d\d\d\d$", x)]
        ndf2 = PDTools(ndf).aa_pd_horizonal_explode(toexplode)
        todrop = []
        toflatten = []
        for col in [x for x in ndf2.columns if regex.findall(r"_\d{4}$", x)]:
            if ndf2[col].iloc[0] in ["end", "start", "match"]:
                todrop.append(col)
            if isinstance(ndf2[col].iloc[0], dict):
                if "text" in ndf2[col].iloc[0]:
                    toflatten.append(col)
        for flatt_ in toflatten:
            ndf2[flatt_] = ndf2[flatt_].apply(lambda x: x["text"])
        ndf2 = ndf2.drop(columns=todrop)
        ndf2columns = [
            "aa_filename",
            "aa_whole_match",
            "aa_line",
            "aa_byte_offset",
            "aa_string",
            "aa_start",
            "aa_end",
        ]
        ndf2.columns = ndf2columns

        ndf2.aa_filename = ndf2.aa_filename.astype("category")
        ndf2.aa_whole_match = ndf2.aa_whole_match.astype("string")
        ndf2.aa_line = ndf2.aa_line.astype("uint32")
        ndf2.aa_byte_offset = ndf2.aa_byte_offset.astype("uint32")
        ndf2.aa_string = ndf2.aa_string.astype("string")
        ndf2.aa_start = ndf2.aa_start.astype("uint32")
        ndf2.aa_end = ndf2.aa_end.astype("uint32")

        return ndf2

    def find_all_in_files_json(
        self,
        re_expression: Union[str, list],
        search_in: Union[str, list],
        outputtype: str = "df",
        binary: bool = True,
        dfa_size: str = "10G",
        ignore_case: bool = True,
        multiline: bool = False,
        multiline_dotall: bool = False,
        outputencoding: str = "utf-8",
    ):
        all_results = []
        search_in = self._to_list(search_in)
        re_expression = self._to_list(re_expression)
        regexstart = PyRipGREP()

        for e in re_expression:
            regexstart.regexp(option=e, multi_allowed=True)
        for temptext in search_in:
            (
                regexstart.json(activated=True)
                .binary(activated=binary)
                .dfa_size_limit(option=dfa_size)
                .ignore_case(option=ignore_case)
                .null_data(activated=True)
                .no_ignore(activated=True)
                .trim(activated=True)
                .block_buffered(activated=True)
                .crlf(activated=True)
                .no_config(activated=True)
                .multiline(activated=multiline)
                .multiline_dotall(activated=multiline_dotall)
                .add_target_file_or_folder(temptext)
            )
            erg = regexstart.run()
            all_results.append(erg)

        try:
            finalresult = self._generator_json(all_results, outputencoding)
            if outputtype == "df":
                finalresult = self._format_json_dataframe(finalresult)
            return finalresult
        except Exception as NotGood:
            return self._return_if_nothing_found(outputtype)

    def find_all_in_var_json(
        self,
        re_expression: Union[str, list],
        variable: Union[str, bin],
        outputtype: str = "df",
        binary: bool = True,
        dfa_size: str = "10G",
        ignore_case: bool = True,
        multiline: bool = False,
        multiline_dotall: bool = False,
        outputencoding: str = "utf-8",
    ):

        re_expression = self._to_list(re_expression)
        regexstart = PyRipGREP()
        for e in re_expression:
            regexstart.regexp(option=e, multi_allowed=True)

        (
            regexstart.json(activated=True)
            .binary(activated=binary)
            .dfa_size_limit(option=dfa_size)
            .ignore_case(activated=ignore_case)
            .null_data(activated=True)
            # .null()
            .no_ignore(activated=True)
            .trim(activated=True)
            .block_buffered(activated=True)
            .crlf(activated=True)
            .no_config(activated=True)
            .multiline(activated=multiline)
            .multiline_dotall(activated=multiline_dotall)
            .add_python_variable_instead_of_file(variable)
        )
        erg = regexstart.run()

        try:
            finalresult = self._generator_json([erg], outputencoding)
            if outputtype == "df":
                finalresult = self._format_json_dataframe(finalresult)
            return finalresult
        except Exception as Notfound:
            print(Notfound)
            return self._return_if_nothing_found(outputtype)

    def _format_output_after_search_in_vars(
        self, result, outputencoding, field_match_separator
    ):
        result3 = self._decode_output_lst(result, outputencoding=outputencoding)
        path_to_search = "<stdin>"
        result4 = self._delete_trash_lst(result3, path_to_search)
        result5 = self._split_field_sep_lst(field_match_separator, result4)
        ziptemp = self._get_splt_list(result5)
        return ziptemp

    def sub_all_in_var(
        self,
        re_expression: Union[str, list],
        repl: str,
        variable: Union[str, list],
        outputtype: str = "df",
        binary: bool = True,
        dfa_size: str = "10G",
        ignore_case: bool = True,
        multiline: bool = False,
        multiline_dotall: bool = False,
        outputencoding: str = "utf-8",
        field_match_separator: str = "ÇÇ",
    ):

        regexstart = PyRipGREP()
        search_for = self._to_list(re_expression)
        for suche in search_for:
            regexstart.regexp(option=suche, activated=True, multi_allowed=True)

        (
            regexstart.binary(activated=binary)
            .byte_offset(activated=True)  # before
            .context_separator(option=" ")
            .dfa_size_limit(option=dfa_size)
            .field_match_separator(option=field_match_separator)
            .ignore_case(activated=ignore_case)
            .null_data(activated=True)
            .line_number(activated=True)
            .no_ignore(activated=True)
            .multiline(activated=multiline)
            .multiline_dotall(activated=multiline_dotall)
            .block_buffered(activated=True)
            .crlf(activated=True)
            .no_config(activated=True)
            .only_matching(activated=True)
            .trim(activated=True)
            .vimgrep(activated=True)
            .replace(option=repl)
            .add_python_variable_instead_of_file(variable)
        )

        result2 = regexstart.run(capture_output=True, save_output_with_shell=None)

        try:
            ziptemp = self._format_output_after_search_in_vars(
                result2, outputencoding, field_match_separator
            )
            df = self._convert_std_lst(ziptemp, outputtype)
            return df
        except Exception as Notfound:
            return self._return_if_nothing_found(outputtype)

    def find_all_in_var(
        self,
        re_expression: Union[str, list],
        variable: Union[str, list],
        outputtype: str = "df",
        binary: bool = True,
        dfa_size: str = "10G",
        ignore_case: bool = True,
        multiline: bool = False,
        multiline_dotall: bool = False,
        outputencoding: str = "utf-8",
        field_match_separator: str = "ÇÇ",
    ):

        regexstart = PyRipGREP()
        search_for = self._to_list(re_expression)
        for suche in search_for:
            regexstart.regexp(option=suche, activated=True, multi_allowed=True)

        (
            regexstart.binary(activated=binary)
            .byte_offset(activated=True)  # before
            .context_separator(option=" ")
            .dfa_size_limit(option=dfa_size)
            .field_match_separator(option=field_match_separator)
            .ignore_case(activated=ignore_case)
            .null_data(activated=True)
            .line_number(activated=True)
            .no_ignore(activated=True)
            .multiline(activated=multiline)
            .multiline_dotall(activated=multiline_dotall)
            .block_buffered(activated=True)
            .crlf(activated=True)
            .no_config(activated=True)
            .only_matching(activated=True)
            .trim(activated=True)
            .vimgrep(activated=True)
            .add_python_variable_instead_of_file(variable)
        )

        result2 = regexstart.run(capture_output=True, save_output_with_shell=None)

        try:
            ziptemp = self._format_output_after_search_in_vars(
                result2, outputencoding, field_match_separator
            )
            df = self._convert_std_lst(ziptemp, outputtype)
            return df
        except Exception as Notfound:
            return self._return_if_nothing_found(outputtype)

    def _format_output_after_search_in_files(
        self, result, outputencoding, field_match_separator, path_to_search
    ):
        result3 = self._decode_output_lst(result, outputencoding=outputencoding)
        result4 = self._delete_trash_lst(result3, path_to_search)
        result5 = self._split_field_sep_lst(field_match_separator, result4)
        ziptemp = self._get_splt_list(result5)
        return ziptemp

    def sub_in_files(
        self,
        re_expression: Union[str, list],
        repl: str,
        path_to_search: Union[str, list],
        outputtype: str = "df",
        binary: bool = True,
        dfa_size: str = "10G",
        ignore_case: bool = True,
        multiline: bool = False,
        multiline_dotall: bool = False,
        outputencoding: str = "utf-8",
        field_match_separator: str = "ÇÇ",
    ):
        regexstart = PyRipGREP()
        search_for = self._to_list(re_expression)
        for suche in search_for:
            regexstart.regexp(option=suche, activated=True, multi_allowed=True)
        (
            regexstart
            # PyRipGREP()
            # .reset_options()
            # .regexp(suchennach, multi_allowed=True)
            .binary(activated=binary)
            .byte_offset(activated=True)  # before
            .context_separator(option=" ")
            .dfa_size_limit(option=dfa_size)
            .field_match_separator(option=field_match_separator)
            .ignore_case(activated=ignore_case)
            .null_data(activated=True)
            .line_number(activated=True)
            .no_ignore(activated=True)
            .multiline(activated=multiline)
            .multiline_dotall(activated=multiline_dotall)
            .block_buffered(activated=True)
            .crlf(activated=True)
            .no_config(activated=True)
            .only_matching(activated=True)
            .trim(activated=True)
            .vimgrep(activated=True)
            .with_filename(activated=True)
            .add_target_file_or_folder(path_to_search)
            .replace(option=repl)
        )
        path_to_search = self._escape_filenames_lst(path_to_search)
        result2 = regexstart.run(capture_output=True, save_output_with_shell=None)
        try:
            ziptemp = self._format_output_after_search_in_files(
                result2, outputencoding, field_match_separator, path_to_search
            )
            df = self._convert_std_lst(ziptemp, outputtype)
            return df
        except Exception as Notfound:
            return self._return_if_nothing_found(outputtype)

    def find_all_in_files(
        self,
        re_expression: Union[str, list],
        path_to_search: Union[str, list],
        outputtype: str = "df",
        binary: bool = True,
        dfa_size: str = "30G",
        ignore_case: bool = True,
        multiline: bool = False,
        multiline_dotall: bool = False,
        outputencoding: str = "utf-8",
        field_match_separator: str = "ÇÇ",
    ):

        regexstart = PyRipGREP()
        search_for = self._to_list(re_expression)
        for suche in search_for:
            regexstart.regexp(option=suche, activated=True, multi_allowed=True)

        (
            regexstart
            # PyRipGREP()
            # .reset_options()
            # .regexp(suchennach, multi_allowed=True)
            .binary(activated=binary)
            .byte_offset(activated=True)  # before
            .context_separator(option=" ")
            .dfa_size_limit(option=dfa_size)
            .field_match_separator(option=field_match_separator)
            .ignore_case(activated=ignore_case)
            .null_data(activated=True)
            .line_number(activated=True)
            .no_ignore(activated=True)
            .multiline(activated=multiline)
            .multiline_dotall(activated=multiline_dotall)
            .block_buffered(activated=True)
            .crlf(activated=True)
            .no_config(activated=True)
            .only_matching(activated=True)
            .trim(activated=True)
            .vimgrep(activated=True)
            .with_filename(activated=True)
            .add_target_file_or_folder(path_to_search)
        )

        path_to_search = self._escape_filenames_lst(path_to_search)
        result2 = regexstart.run(capture_output=True, save_output_with_shell=None)
        try:
            ziptemp = self._format_output_after_search_in_files(
                result2, outputencoding, field_match_separator, path_to_search
            )
            df = self._convert_std_lst(ziptemp, outputtype)
            return df
        except Exception as Notfound:
            return self._return_if_nothing_found(outputtype)


if __name__ == "__main__":

    alltests = True
    if alltests:
        outputtype = "np"

        suchennach = ["weniger", "mehr"]

        filetosearch = [
            r"F:\woerterbuecher\wtxt\xaa.txt",
            r"F:\woerterbuecher\wtxt\xab.txt",
        ]
        np_or_df = "np"
        binary = True
        dfa_size = "30G"
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

        suchennach = ["sein"]

    dfxx = RePatterns().find_all_in_files(
        re_expression=r"\w\w[ener]\b",
        path_to_search=r"F:\woerterbuecher\wtxt\xaa.txt",
        outputtype="df",
        binary=True,
        dfa_size="30G",
        ignore_case=True,
    )
    print(f"{dfxx=}")
