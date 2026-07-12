# ShellCheck Error Codes Reference

Complete reference for ShellCheck diagnostic codes (SC codes).

## Code Categories

### SC1xxx - Parser and Syntax Errors

Fundamental parsing issues and syntax violations.

| Code | Description |
|------|-------------|
| SC1000 | `$` is not used specially and should be escaped |
| SC1001 | This `\o` will be a regular 'o' in this context |
| SC1007 | Remove space after = if trying to assign a value |
| SC1008 | Unrecognized shebang |
| SC1009 | Mentioned parser error was in this... |
| SC1010 | Use semicolon or linefeed before done (or quote to make literal) |
| SC1012 | `\t` is just literal 't' here. Use printf for escape sequences |
| SC1014 | Use `if cmd; then ..` or `if $(cmd)` instead |
| SC1015 | This is a unicode double quote. Use ASCII double quotes |
| SC1016 | This is a unicode single quote. Use ASCII single quotes |
| SC1018 | This is a unicode bullet point. Use ASCII periods |
| SC1033 | Mismatched brackets - expected `[[` but found `[` |
| SC1034 | Mismatched brackets - expected `[` but found `[[` |
| SC1035 | You need a space here |
| SC1036 | Expected `)` but found end of file |
| SC1037 | Braces required for positionals over 9, e.g. `${10}` |
| SC1039 | Expected here-doc line (missing terminator) |
| SC1040 | When using here-doc with quotes, no parameter expansion |
| SC1041 | Found `do` but expected `-` |
| SC1042 | Found `do` where expected select/for/while |
| SC1043 | This seems like an ended here-doc |
| SC1044 | Couldn't find end of here-doc |
| SC1045 | It's not `foo &; bar`, just `foo & bar` |
| SC1046 | Couldn't find `fi` for this `if` |
| SC1047 | Expected `fi` to close `if` statement |
| SC1048 | Can't have empty then clause |
| SC1049 | Expected `do` |
| SC1058 | Expected `do` |
| SC1060 | Expected `do` |
| SC1061 | Couldn't find `done` for this `do` |
| SC1062 | Expected `done` to close `do` |
| SC1064 | Expected `{` to open function definition |
| SC1065 | Trying to define function with arguments? |
| SC1071 | ShellCheck only supports sh/bash/dash/ksh |
| SC1072 | Expected single semicolon in arithmetic for loop |
| SC1073 | Couldn't parse arithmetic expression |
| SC1078 | Did you forget to close this double-quoted string? |
| SC1079 | Missing closing brace for this } |
| SC1081 | Scripts are case sensitive (or try =~ for regex) |
| SC1083 | `{` is literal here. Use `\{` to escape or `${` to start |
| SC1090 | Can't follow non-constant source. Use directive |
| SC1091 | Not following sourced file |
| SC1094 | Parsing of sourced file failed |
| SC1095 | Use `#!/bin/bash` instead of `#!bin/bash` |

### SC2xxx - Semantic and Style Issues

Logic errors, performance concerns, and best practices.

#### Quoting Issues

| Code | Description |
|------|-------------|
| SC2001 | See if you can use `${variable//search/replace}` |
| SC2002 | Useless cat. Consider `cmd < file` or `cmd file` |
| SC2003 | expr is antiquated. Consider using `$((..))` |
| SC2004 | `$`/`${}` unnecessary on arithmetic variables |
| SC2005 | Useless echo. Instead of `echo $(cmd)`, use `cmd` |
| SC2006 | Use `$(...)` notation instead of legacy backticks |
| SC2007 | Use `$((..))` instead of deprecated `$[..]` |
| SC2008 | echo doesn't read from stdin, use cat |
| SC2009 | Consider using pgrep instead of grepping ps |
| SC2010 | Don't use ls | grep. Use glob or find |
| SC2012 | Use find instead of ls to handle non-alphanumeric |
| SC2013 | To read lines, use `while read` or mapfile |
| SC2014 | This will expand once before find runs, not per file |
| SC2015 | Note that `A && B || C` is not if-then-else |
| SC2016 | Expressions don't expand in single quotes |
| SC2017 | Increase by assigning `x=$((x+1))` |
| SC2018 | Use `[:lower:]` to match lowercase |
| SC2019 | Use `[:upper:]` to match uppercase |
| SC2020 | tr expects characters, not words |
| SC2021 | Don't use `a-z` or `A-Z` in tr brackets |
| SC2022 | Use newlines or semicolons between actions |
| SC2024 | sudo doesn't affect redirects |
| SC2025 | Don't use variables in `printf` format string |
| SC2026 | This word is outside any quotes |
| SC2027 | Quotes around $var prevent expansion |
| SC2028 | echo may not expand escape sequences |
| SC2029 | Note that `ssh .. "$VAR"` expands on client |
| SC2030 | Modification in subshell doesn't affect parent |
| SC2031 | var was modified in subshell, parent unaffected |
| SC2032 | Use own script or `sh -c` to nohup |
| SC2033 | Shell functions can't be passed to external commands |
| SC2034 | Variable appears unused (verify or export it) |
| SC2035 | Use `./*glob*` or `-- *glob*` to not start with - |
| SC2036 | If you need absolute path, use `$PWD/foo` |
| SC2037 | Add space between function name and body |
| SC2038 | Use `-print0/-0` or `-d '\n'` with xargs |
| SC2039 | In POSIX sh, this is undefined |
| SC2040 | `#!/bin/sh` wasn't specified but script uses bash |
| SC2041 | This is a literal string (use ranges or classes) |
| SC2043 | This loop will only run once with a constant |
| SC2044 | For loops over find output are fragile |
| SC2045 | Iterating over ls output is fragile |
| SC2046 | Quote this to prevent word splitting |
| SC2048 | Use `"$@"` (with quotes) to prevent whitespace issues |
| SC2049 | `=~` is for regex, use `==` for wildcard |
| SC2050 | This expression is constant, use `if true/false` |
| SC2051 | Bash doesn't support variables in brace ranges |
| SC2053 | Quote RHS of != to prevent glob interpretation |
| SC2054 | Use spaces after `(` and before `)` in arrays |
| SC2055 | You probably wanted `&& here |
| SC2056 | You probably wanted `|| here |
| SC2057 | Unknown binary operator |
| SC2058 | Unknown unary operator |
| SC2059 | Don't use variables in printf format string |
| SC2060 | Quote to prevent word splitting and globbing |
| SC2061 | Quote the regex to prevent shell expansion |
| SC2062 | Quote the regex so it matches literally |
| SC2063 | Grep uses regex, not globs |
| SC2064 | Use single quotes for trap commands |
| SC2065 | This is interpreted as a shell file descriptor |
| SC2066 | This expression won't return failures |
| SC2067 | Missing `;` or `\;` for end of `-exec` command |
| SC2068 | Double quote array expansions to prevent word splitting |
| SC2069 | To redirect stdout+stderr, `2>&1` must be last |
| SC2070 | `-n` doesn't work with unquoted arguments |
| SC2071 | `>` is for string comparisons, use `-gt` for numbers |
| SC2072 | Decimals not supported. Use bc or awk |
| SC2073 | Can't compare numbers with `<` |
| SC2074 | Can't use `=~` in `[`, use `[[` |
| SC2076 | Don't quote regex patterns in `=~` |
| SC2077 | You need spaces around the comparison operator |
| SC2078 | This expression is constant, quote one argument |
| SC2079 | `(( 2.7 ))` may not work as expected |
| SC2080 | Numbers with leading zeros are octal |
| SC2081 | `[ .. ]` can't match globs, use a for loop |
| SC2082 | Use `*` for glob but `.*` for regex |
| SC2083 | Don't add spaces after the slash |
| SC2084 | Remove `$` to add a number to a variable |
| SC2086 | Double quote to prevent globbing and word splitting |
| SC2087 | Quote all here-doc words or escape `$` |
| SC2088 | Tilde does not expand in quotes |
| SC2089 | Quotes/escapes will be literal |
| SC2090 | Quotes/escapes in this variable will be literal |
| SC2091 | Remove surrounding `$()` to call command |
| SC2092 | Remove backticks surrounding assignment |
| SC2093 | Remove `exec &` if script should continue |
| SC2094 | Make sure not to read/write same file in pipeline |
| SC2095 | Command may try to read stdin |
| SC2096 | On most OS, shebangs can't have multiple args |
| SC2097 | This assignment is only in this command's env |
| SC2098 | This expansion won't happen |
| SC2099 | Use `$((..))` for arithmetic |
| SC2100 | Use `$((..))` for arithmetic |

#### Variable Issues

| Code | Description |
|------|-------------|
| SC2102 | Ranges can only match single characters |
| SC2103 | Consider using `cd` with `|| exit` |
| SC2104 | In functions, `return` instead of `continue` |
| SC2105 | `break` only in loops |
| SC2106 | SC2105 but for `break` |
| SC2107 | Instead of `[ -n $foo -o -n $bar ]`, use `[ -n "$foo" ] || [ -n "$bar" ]` |
| SC2108 | In `[]`, use `&&`/`||` instead of `-a`/`-o` |
| SC2109 | Instead of `-a`/`-o`, use `&&`/`||` |
| SC2110 | In `[[]]`, use `&&`/`||` instead of `-a`/`-o` |
| SC2111 | ksh does not support `-a`/`-o` |
| SC2112 | `function` already declares function |
| SC2114 | Avoid `rm -rf` paths with quoted paths |
| SC2115 | Avoid `rm -rf` paths with unquoted variables |
| SC2116 | Useless echo? Instead of `cmd $(echo foo)` |
| SC2117 | Use `su -c cmd` instead of `su; cmd` |
| SC2119 | Use `foo "$@"` to pass args through functions |
| SC2120 | References args but none passed |
| SC2121 | Create array with `arr=(a b)`, not `arr=a arr+=b` |
| SC2122 | `+=` is not possible in numbers |
| SC2123 | PATH is the system path. Use another variable |
| SC2124 | Assigning array to string. Use `"${arr[*]}"` |
| SC2125 | Brace expansion doesn't work in `[` |
| SC2126 | Consider using `grep -c` instead of `grep | wc` |
| SC2128 | Expanding array without index gives first element |
| SC2129 | Consider using `{ cmd1; cmd2; }` redirection |
| SC2130 | `-eq` is for numbers, not strings |
| SC2139 | This expands at definition, not execution |
| SC2140 | Words in braces need quoting for spaces |
| SC2141 | Did you mean IFS=$'\t' or IFS='$(printf '\t')' |
| SC2142 | Aliases can't take arguments. Use functions |
| SC2143 | Use `grep -q` instead of comparing output |
| SC2144 | `-e` doesn't work with globs. Use a for loop |
| SC2145 | Use `"${arr[*]}"` or separate `"${arr[@]}"` |
| SC2146 | This action ignores everything before `-name` |
| SC2147 | Literal tilde in PATH doesn't expand |
| SC2148 | Tips depend on shell. Add shebang |
| SC2149 | Make sure to quote interpolated variables |
| SC2150 | `-exec .. {} +` can't be followed by more flags |
| SC2151 | Only one integer 0-255 for `exit` |
| SC2152 | Can only return 0-255 from functions |
| SC2153 | Possible misspelling of DEFINED |
| SC2154 | var is referenced but not assigned |
| SC2155 | Declare and assign separately to avoid masking |
| SC2156 | Inject argument via `..`- `{}` doesn't expand |
| SC2157 | Argument to implicit `-n` is a literal string |
| SC2158 | `[ false ]` is true. Use `if !` or `[[]]` |
| SC2159 | `[ 0 ]` is true. Use `(( ))` for arithmetic |
| SC2160 | Use true command instead of `[ 1 ]` |
| SC2161 | Instead of `[ expr ]`, use `((expr))` or `[[ n -gt 0 ]]` |
| SC2162 | read without -r mangles backslashes |
| SC2163 | This does not export the variable |
| SC2164 | Use `cd .. || exit` in case cd fails |
| SC2165 | Wrap this in a loop? Use break/exit correctly |
| SC2166 | Prefer `[ p ] && [ q ]` in sh |
| SC2167 | This doesn't assign the output of cmd |
| SC2168 | local is only valid in functions |
| SC2169 | In dash, this is undefined |
| SC2170 | Numerical `-eq` used for string |
| SC2171 | Expected test after `elif` |
| SC2172 | Trapping signals by number is not portable |
| SC2173 | SIGKILL can't be trapped |
| SC2174 | mkdir -p -m creates only final dir with perms |
| SC2175 | Quote to prevent word splitting |
| SC2176 | time is undefined for pipelines |
| SC2177 | time is undefined for compound |
| SC2178 | Variable was used as array but assigned string |
| SC2179 | Use array+=("item") to append to arrays |
| SC2180 | Bash brace expansion is not supported |
| SC2181 | Check exit code directly, not `$?` |
| SC2182 | This printf format doesn't match args |
| SC2183 | printf format string has more format specs than args |
| SC2184 | Quote args to unset to handle special chars |
| SC2185 | Some finds don't accept path after expression |
| SC2186 | tempfile is deprecated. Use mktemp |
| SC2187 | Ash scripts need `--` before `-e` |
| SC2188 | This redirection has nothing |
| SC2189 | You can't have | before redirect in command |
| SC2190 | Elements in associative array need index |
| SC2191 | Elements in indexed arrays need no index |
| SC2192 | This array element has no value |
| SC2193 | This comparison is constant |
| SC2194 | This word is constant |
| SC2195 | Pattern won't match with `/` |
| SC2196 | egrep is non-standard and deprecated |
| SC2197 | fgrep is non-standard and deprecated |
| SC2198 | Arrays don't work in `[=]`. Use `[[==]]` |
| SC2199 | Arrays expand separately |
| SC2200 | Glob used where integer expected |
| SC2201 | This glob only matches paths with `/` |
| SC2202 | Globs are lowercase. Use `echo 'text'` |
| SC2203 | Glob only matches if expanded |
| SC2204 | `(...)` is a subshell. Did you mean `[...]` |

### SC3xxx - POSIX Compatibility

Warnings for non-POSIX features in `sh` scripts.

| Code | Description |
|------|-------------|
| SC3001 | In POSIX sh, `$'..'` is undefined |
| SC3002 | In POSIX sh, extglob is undefined |
| SC3003 | In POSIX sh, `$'...'` is undefined |
| SC3004 | In POSIX sh, `$".."` is undefined |
| SC3005 | In POSIX sh, `{..}` brace expansion is undefined |
| SC3006 | In POSIX sh, `[[` is undefined |
| SC3007 | In POSIX sh, `((` is undefined |
| SC3008 | In POSIX sh, `select` is undefined |
| SC3009 | In POSIX sh, `&>` is undefined |
| SC3010 | In POSIX sh, `coproc` is undefined |
| SC3011 | In POSIX sh, `here-strings` are undefined |
| SC3012 | In POSIX sh, lexicographic comparison is undefined |
| SC3013 | In POSIX sh, `-v` is undefined |
| SC3014 | In POSIX sh, `=~` is undefined |
| SC3015 | In POSIX sh, `>&X` redirects are undefined |
| SC3016 | In POSIX sh, `>&filename` is undefined |
| SC3017 | In POSIX sh, `<(cmd)` is undefined |
| SC3018 | In POSIX sh, process substitution is undefined |
| SC3019 | In POSIX sh, `readonly` scoping is undefined |
| SC3020 | In POSIX sh, `&>` is undefined |
| SC3024 | In POSIX sh, `-o pipefail` is undefined |
| SC3028 | In POSIX sh, `BASHPID` is undefined |
| SC3030 | In POSIX sh, arrays are undefined |
| SC3033 | In POSIX sh, `declare` is undefined |
| SC3035 | In POSIX sh, `read -r` with arrays is undefined |
| SC3036 | In POSIX sh, `echo -n` is undefined |
| SC3037 | In POSIX sh, `echo -e` is undefined |
| SC3039 | In POSIX sh, `let` is undefined |
| SC3040 | In POSIX sh, `set -o` is undefined |
| SC3044 | In POSIX sh, `local` is undefined |
| SC3045 | In POSIX sh, `read -t` is undefined |
| SC3046 | In POSIX sh, `source` is undefined |
| SC3047 | In POSIX sh, this signal is undefined |
| SC3048 | In POSIX sh, `printf %q` is undefined |
| SC3050 | In POSIX sh, `mapfile` is undefined |
| SC3054 | In POSIX sh, array references are undefined |
| SC3055 | In POSIX sh, array key expansion is undefined |
| SC3056 | In POSIX sh, `+=` is undefined |
| SC3057 | In POSIX sh, string indexing is undefined |
| SC3058 | In POSIX sh, `${var/pat/str}` is undefined |
| SC3059 | In POSIX sh, indirect expansion is undefined |
| SC3060 | In POSIX sh, `${var:start}` is undefined |

## Severity Levels

ShellCheck categorizes warnings by severity:

| Level | Description |
|-------|-------------|
| **error** | Definite bugs or syntax errors |
| **warning** | Likely issues that could cause problems |
| **info** | Suggestions for better practices |
| **style** | Purely stylistic suggestions |

## Wiki Links

Each code has detailed documentation at:
`https://www.shellcheck.net/wiki/SCXXXX`

For example: https://www.shellcheck.net/wiki/SC2086
