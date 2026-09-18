# GGML GGUF File Format Vulnerabilities

- Source: https://www.databricks.com/blog/ggml-gguf-file-format-vulnerabilities
- Published: 2024-03-22
- Authors: Neil Archibald
- Categories: engineering, open-source
- Images: 0 total, 0 extracted as architecture

The [GGUF file format](https://github.com/ggerganov/ggml/) is a binary file format used for storing and loading model weights for the GGML library. The library documentation describes the format as follows:

*"GGUF is a file format for storing models for inference with GGML and executors based on GGML. GGUF is a binary format that is designed for fast loading and saving of models, and for ease of reading. Models are traditionally developed using PyTorch or another framework, and then converted to GGUF for use in GGML."*

The *GGUF* format has recently become popular for distributing trained machine learning models, and has become one of the most commonly used formats for Llama-2 when utilizing the model from a low level context. There are multiple vectors that can be used to provide data to this loader, including llama.cpp, the python [llm](https://llm.datasette.io/en/stable/) module, and the [ctransformers](https://github.com/marella/ctransformers) library when loading gguf files, such as those from Huggingface.

The GGML library performs insufficient validation on the input file and, therefore, contains a selection of potentially exploitable memory corruption vulnerabilities during parsing. An attacker could leverage these vulnerabilities to execute code on the victim's computer via serving a crafted `gguf` file.

In this blog, we will look at some of the heap overflows which are fairly easy to exploit. Since there is almost no bounds checking done on the file, there are numerous other cases where allocations are performed with unbounded user input and wrapped values. It is also worth noting that very few return values are checked throughout the code base, including the memory allocations. All the heap overflows are reachable via the `gguf_init_from_file()` entry point.

## Timeline

1. Jan 23rd 2024: Vendor Contacted, bugs reported
2. Jan 25th 2024: CVE's Requested
3. Jan 28th 2024: Reviewed Fixes in GGML Github
4. Jan 29th 2024: Patches Merged into master branch

## CVE-2024-25664 Heap Overflow #1: Unchecked KV Count

The entry point to the library, when loading a saved model, is typically via the `gguf_init_from_file()` function (shown annotated below). This function begins by reading the gguf header from the file before checking for the magic value "`GGUF`". After this, the key-value pairs within the file are read and parsed.

[https://github.com/ggerganov/ggml/blob/faab2af1463aa556899b72 1289efcbf50c557f55/src/ggml.c#L19215](https://github.com/ggerganov/ggml/blob/faab2af1463aa556899b721289efcbf50c557f55/src/ggml.c#L19215)

The contents of the wrapped allocation are an array of `*gguf_kv*` structures, which are used to store key-value pairs of data read from the file. The definition of the structure is as follows:

[https://github.com/ggerganov/ggml/blob/faab2af1463aa556899b72 1289efcbf50c557f55/src/ggml.c#L19133](https://github.com/ggerganov/ggml/blob/faab2af1463aa556899b721289efcbf50c557f55/src/ggml.c#L19133)

This allows us to overwrite adjacent memory with either data we control using the value field or a pointer to data we control in the case of the key field. These are fairly powerful primitives for heap exploitation. Due to the nature of the parsing, it is also possible to manipulate the heap state in a fairly arbitrary manner. This should also make exploitation easier.

The following PoC code causes an allocation of `0xe0` while having an `n_kv` value of `0x55555555555555a`, which is used as the loop counter writing into the chunk. Each write is `0x30` sized (`sizeof(struct gguf_kv)`) and this results in heap memory being smashed containing our `0x500 kv's`. To terminate the loop, we simply end the file early, resulting in an EOF read and an error condition. The subsequent usage of the heap results in a failed checksum due to the overflow and an `abort()` error message.

## CVE-2024-25665 Heap Overflow #2: Reading string types

Another potentially exploitable heap overflow vulnerability exists in the function `gguf_fread_str(),` which is used repeatedly to read string-type data from the file.

As you can see in the code below, this function reads a length-encoded string directly from the file with no validation. Firstly, the length of the string is read using `gguf_fread_el()`. Next, an allocation of the arbitrary input size + 1 is performed. By providing a size of `0xffffffffffffffff`, the addition will cause the value to wrap back to 0. When the allocator receives this size it will return a chunk sized as the smallest possible quanta used by the allocator. After this is done, a copy will be performed using the `fread*()*` function using the large unwrapped size.

[https://github.com/ggerganov/ggml/blob/faab2af1463aa556899b72 1289efcbf50c557f55/src/ggml.c#L19177](https://github.com/ggerganov/ggml/blob/faab2af1463aa556899b721289efcbf50c557f55/src/ggml.c#L19177)

## CVE-2024-25666 Heap Overflow #3: Tensor count unchecked

A very similar heap overflow to #1 exists when parsing the `gguf_tensor_infos` in the file. The `ctx->header.n_tensors` value is unchecked and multiplied once again by the size of a struct, resulting in a wrap and a smaller allocation. Following this, a loop copies each element in turn, resulting in a heap overflow. The code below shows this vulnerability.

[https://github.com/ggerganov/ggml/blob/faab2af1463aa556899b72 1289efcbf50c557f55/src/ggml.c#L19345](https://github.com/ggerganov/ggml/blob/faab2af1463aa556899b721289efcbf50c557f55/src/ggml.c#L19345)

## CVE-2024-25667 Heap Overflow #4: User-supplied Array Elements

When unpacking the `kv` values from the file, one of the types that can be unpacked is the array type (`GGUF_TYPE_ARRAY`). When parsing arrays, the code reads the type of the array, followed by the number of elements of that type. It then multiplies the type size from the `GGUF_TYPE_SIZE` array with the number of elements to calculate the allocation size to store the data. Once again, since the number of array elements is user-supplied and arbitrary, this calculation can wrap, resulting in a small allocation of memory, followed by a large copy loop. Due to the compact nature of the array data, this provides a very controlled overflow over heap contents, which can be terminated by a failed file read.

[https://github.com/ggerganov/ggml/blob/faab2af1463aa556899b72 1289efcbf50c557f55/src/ggml.c#L19297](https://github.com/ggerganov/ggml/blob/faab2af1463aa556899b721289efcbf50c557f55/src/ggml.c#L19297)

## CVE-2024-25668 Heap Overflow #5: Unpacking kv string type arrays

Another heap overflow issue exists during the array kv unpacking when dealing with arrays of string type. When parsing strings, once again, an element count is read directly from the file unchecked. This value is multiplied by the size of the `gguf_str` struct, resulting in a wrap and a small allocation relative to n. Following this, a loop is performed up to the n value in order to populate the chunk. This results in an out-of-bounds write of the string struct contents.

[https://github.com/ggerganov/ggml/blob/faab2af1463aa556899b72 1289efcbf50c557f55/src/ggml.c#L19318](https://github.com/ggerganov/ggml/blob/faab2af1463aa556899b721289efcbf50c557f55/src/ggml.c#L19318)

### Unbounded Array Indexing

During the parsing of arrays within the GGUF file, as mentioned above, the required size of a type is determined for allocation via the `GGUF_TYPE_SIZE[]` array (shown below).

[https://github.com/ggerganov/ggml/blob/faab2af1463aa556899b72 1289efcbf50c557f55/src/ggml.c#L19076](https://github.com/ggerganov/ggml/blob/faab2af1463aa556899b721289efcbf50c557f55/src/ggml.c#L19076)

By indexing into the array, the appropriate size is returned in order to calculate the allocation size via multiplication.

The index used to access this array is read directly from the file and is not sanitized, therefore, an attacker could provide an index outside the bounds of this array, returning a size that causes an integer wrap. This is used in both an allocation and a copy.

The following code demonstrates this path:

[https://github.com/ggerganov/ggml/blob/faab2af1463aa556899b72 1289efcbf50c557f55/src/ggml.c#L19300](https://github.com/ggerganov/ggml/blob/faab2af1463aa556899b721289efcbf50c557f55/src/ggml.c#L19300)

## Conclusion

These vulnerabilities would provide [yet another way](https://www.legitsecurity.com/blog/tens-of-thousands-of-developers-were-potentially-impacted-by-the-hugging-face-aijacking-attack) for an attacker to utilize machine learning models to distribute malware and compromise developers. The security posture of this new and rapidly growing field of research greatly benefits from a more rigorous approach to security review. In that frame, Databricks worked closely with the GGML.ai team, and together we quickly addressed these issues. The patches have been available since commit [6b14d73](https://github.com/ggerganov/ggml/tree/6b14d738d9100c50c199a3b1aaa960f633904476) which fixes all 6 vulnerabilities discussed in this post.
