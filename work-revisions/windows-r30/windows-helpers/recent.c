// Windows x64, Quartet build 26908524. Keep references to live inventory rows, newest first.
#include <windows.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <wchar.h>

typedef void *Obj;
typedef uintptr_t Handle;
enum { CAPACITY = 30, RECENT_TAB = 8, RECENT_FILTER = 12 };
static Handle newest[CAPACITY];
static unsigned used;
static Obj entry_class;
static Handle pending_gear;
static Obj rendering_inventory;
static HMODULE game(void) { return GetModuleHandleW(L"GameAssembly.dll"); }

#ifndef GAME_FUNCTION
#define GAME_FUNCTION(rva, type) ((type)((uintptr_t)game() + (rva)))
#endif
#define EXPORT __declspec(dllexport)
typedef void (*Add)(Obj, Obj, int, Obj);
typedef Obj (*ResolveItem)(Obj, Obj);
typedef Obj (*Equip)(Obj, int, Obj, Obj, Obj);
typedef Obj (*ApplyFilter)(Obj, Obj, int, Obj);
typedef struct { Obj title, icon; } Caption;
typedef Caption *(*Lookup)(Caption *, Obj, int, Obj);
typedef Obj (*Builder)(Obj, Obj);
typedef void (*SetValue)(Obj, Obj, Obj);

#define API_LIST(X) \
 X(Obj,domain_get,(void)) X(Obj,domain_assembly_open,(Obj,const char *)) \
 X(Obj,assembly_get_image,(Obj)) X(Obj,class_from_name,(Obj,const char *,const char *)) \
 X(Obj,class_get_nested_types,(Obj,void **)) X(const char *,class_get_name,(Obj)) \
 X(Obj,class_get_method_from_name,(Obj,const char *,int)) X(Obj,object_new,(Obj)) \
 X(Obj,runtime_invoke,(Obj,Obj,void **,Obj *)) X(Handle,gchandle_new,(Obj,bool)) \
 X(void,gchandle_free,(Handle)) X(Obj,gchandle_get_target,(Handle)) \
 X(Obj,array_new,(Obj,uintptr_t)) X(void,gc_wbarrier_set_field,(Obj,Obj *,Obj)) \
 X(Obj,class_get_type,(Obj)) X(Obj,type_get_object,(Obj)) X(Obj,object_get_class,(Obj)) \
 X(Obj,class_get_methods,(Obj,void **)) X(Obj,class_get_parent,(Obj)) \
 X(const char *,method_get_name,(Obj)) X(uint32_t,method_get_param_count,(Obj)) \
 X(Obj,method_get_param,(Obj,uint32_t)) X(int,type_get_type,(Obj)) X(bool,method_is_generic,(Obj)) \
 X(Obj,string_new_utf16,(const wchar_t *,int)) \
 X(Obj,class_get_field_from_name,(Obj,const char *)) X(void,field_get_value,(Obj,Obj,void *))
#define DECLARE(ret,name,args) static ret (*name)args;
API_LIST(DECLARE)

static bool ready(void) {
    if (entry_class) return true;
    HMODULE module = game();
    if (!module) return false;
#define LOAD(ret,name,args) name = (ret (*)args)(uintptr_t)GetProcAddress(module,"il2cpp_" #name); if (!name) return false;
    API_LIST(LOAD)
#undef LOAD
    Obj assembly = domain_assembly_open(domain_get(),"Assembly-CSharp");
    if (!assembly) return false;
    Obj manager = class_from_name(assembly_get_image(assembly),"Services.Inventory","InventoryManager");
    if (!manager) return false;
    void *iter = NULL;
    for (Obj nested; (nested = class_get_nested_types(manager,&iter)) != NULL;) {
        if (strcmp(class_get_name(nested),"Entry") == 0) {
            entry_class = nested;
            break;
        }
    }
    return entry_class != NULL;
}

// These fields and generic method slots are from the fingerprinted Windows build.
static Obj reference(Obj self, size_t offset) {
    return self ? *(Obj *)((char *)self+offset) : NULL;
}
static int integer(Obj self, size_t offset) {
    return self ? *(int *)((char *)self+offset) : 0;
}
#ifndef GAME_METADATA
#define GAME_METADATA(rva) reference(game(),(rva))
#endif
typedef bool (*Contains)(Obj,Obj,Obj);
typedef Obj (*Find)(Obj,Obj,Obj);
static Obj live_entry(Obj inventory, Obj item) {
    Obj dictionary = reference(inventory,0x18);
    Obj id = reference(item,0x10);
    if (!dictionary || !id) return NULL;
    Obj contains = GAME_METADATA(0x3be2038), get = GAME_METADATA(0x3be2678);
    if (!contains || !get || !GAME_FUNCTION(0xee4520,Contains)(dictionary,id,contains)) return NULL;
    return GAME_FUNCTION(0xee8c60,Find)(dictionary,id,get);
}
static int quantity(Obj entry) { return integer(reference(entry,0x18),0x10); }
static void forget_gear(void) {
    if (pending_gear) gchandle_free(pending_gear);
    pending_gear = 0;
}
static void remove_at(unsigned i) {
    gchandle_free(newest[i]);
    used--;
    memmove(newest+i,newest+i+1,(used-i)*sizeof(Handle));
    newest[used]=0;
}
static void reset_shortcut(void);
static void clear_history(void) {
    reset_shortcut();
    while (used) remove_at(used-1);
    forget_gear();
}
static void prune(void) {
    for (unsigned i=used;i>0;i--)
        if (quantity(gchandle_get_target(newest[i-1]))<=0) remove_at(i-1);
}
static void record(Obj inventory,Obj item,int count) {
    if (!item || count<=0 || !ready()) return;
    prune();
    Obj row=live_entry(inventory,item);
    if (quantity(row)<=0) return;
    Handle handle=gchandle_new(row,false);
    if (!handle) return;
    for (unsigned i=0;i<used;i++) {
        if (gchandle_get_target(newest[i])==row) { remove_at(i); break; }
    }
    if (used==CAPACITY) remove_at(used-1);
    memmove(newest+1,newest,used*sizeof(Handle));
    newest[0]=handle;
    used++;
}
EXPORT void award_item(Obj inventory, Obj item, int count, Obj method) {
    GAME_FUNCTION(0x572a50,Add)(inventory,item,count,method);
    record(inventory,item,count);
}

EXPORT void award_id(Obj inventory, Obj id, int count, Obj method) {
    // This is exactly the string overload's conversion and delegation.
    Obj item = GAME_FUNCTION(0x572740,ResolveItem)(id,NULL);
    award_item(inventory,item,count,method);
}

EXPORT Obj buy_equipped(Obj hero, int slot, Obj item, Obj inventory, Obj method) {
    Obj previous = GAME_FUNCTION(0x599b10,Equip)(hero,slot,item,inventory,method);
    record(inventory,item,1);
    return previous;
}

EXPORT Obj load_builder(Obj self, Obj method) {
    clear_history();
    return GAME_FUNCTION(0xba4d70,Builder)(self,method);
}
EXPORT void clear_value(Obj self, Obj value, Obj method) {
    clear_history();
    GAME_FUNCTION(0xef0810,SetValue)(self,value,method);
}

EXPORT Obj list_inventory(Obj party,Obj method) {
    rendering_inventory=GAME_FUNCTION(0x57e0a0,Builder)(party,method);
    return rendering_inventory;
}
EXPORT Obj filter_items(Obj list, Obj items, int filter, Obj method) {
    if (filter != RECENT_FILTER)
        return GAME_FUNCTION(0x69f4f0,ApplyFilter)(list,items,filter,method);
    if (!ready())
        return GAME_FUNCTION(0x69f4f0,ApplyFilter)(list,items,11,method);
    prune();
    Obj visible[CAPACITY];
    unsigned length=0;
    for (unsigned i=0;i<used;i++) {
        Obj row=gchandle_get_target(newest[i]);
        if (row==live_entry(rendering_inventory,reference(row,0x10))) visible[length++]=row;
    }
    Obj array = array_new(entry_class,length);
    if (!array) return GAME_FUNCTION(0x69f4f0,ApplyFilter)(list,items,11,method);
    // Il2CppArraySize's reference vector begins at 0x20 on this x64 build.
    Obj *slots = (Obj *)((unsigned char *)array+0x20);
    for (unsigned i=0; i<length; i++) {
        Obj entry = visible[i];
        slots[i] = entry;
        gc_wbarrier_set_field(array, slots+i, entry);
    }
    return array;
}

static bool equipment(Obj entry) {
    Obj data=reference(reference(entry,0x10),0x30);
    int slot=integer(data,0x10);
    return slot>=2 && slot<=5;
}
static bool recent_page(Obj list) { return integer(reference(list,0x50),0x10)==RECENT_FILTER; }
static bool can_equip(void) {
    Obj gate=GAME_FUNCTION(0x6b6880,Builder)(NULL,NULL);
    return gate && *((unsigned char *)gate+0x10)!=0;
}
EXPORT bool enable_recent_gear(Obj list,Obj entry) {
    return recent_page(list) && equipment(entry) && quantity(entry)>0 && can_equip();
}
typedef void (*MenuCommand)(Obj,Obj);
typedef void (*SelectEntry)(Obj,Obj,Obj);
typedef void (*SelectSlot)(Obj,int,Obj);
#include "preview.h"
static bool english(void) {
    wchar_t path[32768];
    DWORD length = GetModuleFileNameW(game(),path,32768);
    if (!length || length >= 32768) return false;
    wchar_t *name = wcsrchr(path,L'\\');
    if (!name || 32768-(name+1-path) < 24) return false;
    wcscpy(name+1,L"QuartetZh-language.txt");
    HANDLE f = CreateFileW(path,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
                           NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
    if (f == INVALID_HANDLE_VALUE) return false;
    char buf[5];
    DWORD n=0;
    BOOL ok = ReadFile(f,buf,sizeof(buf),&n,NULL);
    CloseHandle(f);
    return ok && ((n==2 && !memcmp(buf,"en",2)) || (n==3 && !memcmp(buf,"en\n",3)));
}

EXPORT Caption *tab_caption(Caption *out, Obj dict, int key, Obj method) {
    Lookup original = GAME_FUNCTION(0x1542680,Lookup);
    original(out,dict,key==RECENT_TAB ? 0 : key,method);
    if (key==RECENT_TAB && ready()) {
        const wchar_t *label = english() ? L"Recent" : L"最近获得";
        out->title = string_new_utf16(label,(int)wcslen(label));
        static const wchar_t icon[] = L"ico_hourglass";
        out->icon = string_new_utf16(icon,(int)(sizeof(icon)/sizeof(*icon)-1));
    }
    return out;
}
