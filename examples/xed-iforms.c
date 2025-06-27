#include "xed/xed-interface.h"
#include <stdio.h>
int main(int argc, char** argv);
int main(int argc, char** argv) {
    (void)argc;
    (void)argv;
    xed_tables_init();

    printf("IFORM, ICLASS, INTEL_NAME, ATT_NAME, CATEGORY, EXTENSION, ISA_SET\n");

    // Iterate over all iclasses
    for (xed_iclass_enum_t iclass = 0; iclass < XED_ICLASS_LAST; ++iclass) {
        xed_uint32_t niforms = xed_iform_max_per_iclass(iclass);
        xed_uint32_t iform_first = xed_iform_first_per_iclass(iclass);

        // Iterate over all iforms for this iclass
        for (xed_uint32_t i = 0; i < niforms; ++i) {
            xed_iform_enum_t iform = iform_first + i;

            // Get various ISA properties for this iform
            xed_iclass_enum_t i_iclass = xed_iform_to_iclass(iform);
            xed_category_enum_t category = xed_iform_to_category(iform);
            xed_extension_enum_t extension = xed_iform_to_extension(iform);
            xed_isa_set_enum_t isa_set = xed_iform_to_isa_set(iform);
            const char* iclass_name = xed_iform_to_iclass_string_intel(iform);
            const char* iclass_name_att = xed_iform_to_iclass_string_att(iform);

            // String conversions for enums
            const char* cat_str = xed_category_enum_t2str(category);
            const char* ext_str = xed_extension_enum_t2str(extension);
            const char* isa_str = xed_isa_set_enum_t2str(isa_set);
            const char* iform_str = xed_iform_enum_t2str(iform);

            printf("%s, %s, %s, %s, %s, %s, %s\n",
                iform_str,
                xed_iclass_enum_t2str(i_iclass),
                iclass_name,
                iclass_name_att,
                cat_str,
                ext_str,
                isa_str
            );
        }
    }
    return 0;
}