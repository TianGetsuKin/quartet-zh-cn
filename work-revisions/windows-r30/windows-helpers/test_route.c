// Exercise the compiled routing functions with isolated Unity services and party layouts.
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
static void *fake(unsigned);
#define GAME_FUNCTION(r,t) ((t)fake(r))
#define GAME_METADATA(r) ((void *)(uintptr_t)r)
#include "recent.c"

typedef struct {Obj fields[48];} Node;
static Node menu,pulse,ui,list,filter,gate,entry,count,item,data,ctl,rect,summary,slotList,values;
static Node card[3],button[3],indexNode[3],heroes[3],cards,buttons,controllers,equipList,slotRender;
static Node home,picker,gear,preview,es;
static Obj current,stack[8];static int depth,confirmations,clears,focused,errors,equippedSlot;
static int picker_opens,pops,toasts;
static bool allowed[3],isHidden[3],slotFull[6],locked[6];
static int completed;
static Node bag,dict,heroSubject,party,slotPanel,id,otherId,otherItem,otherEntry,otherCount;
static Node listContainer,rowB,renderB,boxedIndex,thirdItem;
static Obj shownHero,chosenRow;
static int activeSlot,siblingIndex;
static Obj field_by(Obj type,const char *s){(void)type;return (Obj)s;}
static void field_value(Obj o,Obj f,void *out){
    if(o==&equipList && !strcmp(f,"container")){*(Obj*)out=&listContainer;return;}
    if(o==&slotPanel && !strcmp(f,"heroOb")){*(Obj*)out=&heroSubject;return;}
    if(o==&ctl && !strcmp(f,"selectedSlot")){*(int*)out=activeSlot;return;}
    if(o==&pulse && !strcmp(f,"partyService")){*(Obj*)out=&party;return;}
    *(Obj*)out=NULL;
}
static bool has(Obj o,Obj key,Obj mi){(void)mi;return o==&dict && (key==&id || key==&otherId);}
static Obj getentry(Obj o,Obj key,Obj mi){assert(o==&dict);(void)mi;return key==&id?&entry:&otherEntry;}
static Obj pop(Obj,int,Obj);
static uintptr_t geth(Obj p,bool pin){assert(!pin);return (uintptr_t)p;}
static Obj deref(Handle h){return (Obj)h;}
static void freeh(Handle h){assert(h);}
static Obj self(Obj p){return p;}
static Obj dummy(Obj o,const char *s){(void)s;return o;}
static Obj classby(Obj a,const char *ns,const char *name){(void)a;(void)ns;return (Obj)name;}
static Obj domain(void){return &es;}
static Obj method(Obj o,const char *s,int n){(void)o;(void)n;return (Obj)s;}
static Obj methods(Obj o,void **it){(void)o;if(!*it)return *it="GetComponentsInChildren";
    if(!strcmp(*it,"GetComponentsInChildren"))return *it="GetComponentInParent";return NULL;}
static bool nongeneric(Obj m){(void)m;return false;}
static uint32_t two(Obj m){(void)m;return 2;}
static Obj param(Obj m,uint32_t i){assert(i==1);return m;}
static int boolean_type(Obj m){(void)m;return 2;}
static const char *name_of(Obj m){return m;}
static void arr(Node *n,int len){n->fields[3]=(Obj)(uintptr_t)len;}
static Obj invoke(Obj m,Obj o,void **args,Obj *ex){
    *ex=NULL;const char *s=m;
    if(!strcmp(s,"get_current"))return &es;
    if(!strcmp(s,"get_currentSelectedGameObject"))return current;
    if(!strcmp(s,"get_Inventory") && o==&party)return &bag;
    if(!strcmp(s,"get_Value") && o==&heroSubject)return shownHero;
    if(!strcmp(s,"get_transform") && o==&item)return &rowB;
    if(!strcmp(s,"get_parent") && o==&rowB)return &listContainer;
    if(!strcmp(s,"GetComponentInParent") && o==&listContainer && !strcmp(args[0],"ScrollRect"))return &listContainer;
    if(!strcmp(s,"set_verticalNormalizedPosition") && o==&listContainer){assert(*(float*)args[0]==1.0f);return NULL;}
    if(!strcmp(s,"get_lastItem") && o==&renderB)return &item;
    if(!strcmp(s,"GetSiblingIndex") && o==&rowB){boxedIndex.fields[2]=(Obj)(uintptr_t)siblingIndex;return &boxedIndex;}
    if(!strcmp(s,"SetAsFirstSibling") && o==&rowB){siblingIndex=0;return NULL;}
    if(!strcmp(s,"SetSiblingIndex") && o==&rowB){siblingIndex=*(int*)args[0];return NULL;}
    if(!strcmp(s,"get_transform") || !strcmp(s,"get_root"))return &menu;
    if(!strcmp(s,"GetComponentsInChildren")){
        if(!strcmp(args[0],"UIItemChoiceRender")){buttons.fields[4]=&renderB;return &buttons;}
        if(!strcmp(args[0],"UIPartyIndex")){
            // An inactive summary exposes no cards unless explicitly included.
            if(depth==1 && !*(bool*)args[1])return NULL;
            return &cards;
        }
        if(!strcmp(args[0],"FieldMenuEquipController"))return &controllers;
        int i=o==&slotRender?0:(int)((Node*)o-indexNode);
        assert(i>=0 && i<3);buttons.fields[4]=&button[i];return &buttons;
    }
    for(int i=0;i<3;i++){
        if(!strcmp(s,"get_gameObject") && o==&indexNode[i])return &card[i];
        if(!strcmp(s,"Select") && o==&button[i]){current=&card[i];return NULL;}
        if(!strcmp(s,"SetActive") && o==&card[i]){isHidden[i]=!*(bool*)args[0];return NULL;}
    }
    abort();
}
static Obj got_pulse(Obj m){(void)m;return &pulse;}
static Obj top(Obj u,Obj m){assert(u==&ui && !m);return stack[depth-1];}
static Obj getgate(Obj x,Obj m){(void)x;(void)m;return &gate;}
static Obj gethero(Obj idx,Obj m){(void)m;return &heroes[(Node*)idx-indexNode];}
static bool usable(Obj h,Obj i,Obj m){assert((i==&item || i==&otherItem) && !m);return allowed[(Node*)h-heroes];}
static Obj slots(Obj i,Obj m){assert((i==&item || i==&otherItem) && !m);return &slotList;}
static bool lockslot(Obj h,int s,Obj m){(void)h;(void)m;return locked[s];}
static Obj getequip(Obj h,int s,Obj m){(void)h;(void)m;return slotFull[s]?&item:NULL;}
static void command(Obj a,Obj m){assert(a==&menu && !m);picker_opens++;stack[depth++]=&picker;}
static void nativehero(Obj a,Obj m){assert(a==&menu && !m);if(!*((bool *)((char *)a+0x21)))pop(&ui,0,NULL);stack[depth++]=&gear;}
static void submit(Obj a,Obj m){choose_hero(a,m,nativehero);}
static Obj render(Obj a,int s,Obj m){(void)a;(void)m;equippedSlot=s;return &slotRender;}
static void adjust(Obj a,int s,Obj m){assert(a==&ctl && s==equippedSlot && !m);}
static void openlist(Obj a,int s,Obj m){adjust(a,s,m);activeSlot=s;shownHero=route.hero;stack[depth++]=&preview;}
static void openslot(Obj a,int s,Obj m){choose_slot(a,s,m,openlist);}
static void focus(Obj a,Obj i,Obj m){assert((a==&list || a==&equipList) && i==&item && !m);focused++;current=i;}
static Obj rawpop(Obj u,int hint,Obj m){(void)hint;assert(u==&ui && !m && depth>1);pops++;--depth;return stack[depth-1];}
static Obj pop(Obj u,int hint,Obj m){return pop_shortcut(u,hint,m,rawpop);}
static void finish(Obj u,Obj m){assert(u==&ui && !m && depth==1);current=NULL;completed++;}
static void clear(Obj h,Obj m){assert(h && !m);clears++;}
static void bad(Obj h,Obj m){assert(h==&ui && !m);errors++;}
static void equip(Obj c,Obj e,Obj m){assert(c==&ctl && !m && (e==&entry || e==&otherEntry));chosenRow=e;((Node*)reference(e,0x18))->fields[2]=0;confirmations++;pop(&ui,0,NULL);}
static void unexpected(Obj a,Obj b,Obj c){(void)a;(void)b;(void)c;abort();}
static Obj toast_string(const wchar_t *s,int n){assert(n==(int)wcslen(s));return (Obj)s;}
static void toast(Obj u,Obj text,Obj callback,Obj method){
    assert(u==&ui && !callback && !method && depth==1);
    assert(!wcscmp(text,english()?L"No one in your party can equip this.":L"当前队伍无人能装备"));
    toasts++;
}
static void *fake(unsigned r){
    switch(r){
#define F(n,f) case n:return (void*)f
    F(0x6b6880,getgate);F(0x10056c0,got_pulse);F(0x562050,top);F(0x671810,command);
    F(0xee4520,has);F(0xee8c60,getentry);
    F(0x6b7310,gethero);F(0x5968c0,usable);F(0x5724c0,slots);F(0x597f60,lockslot);
    F(0x596e90,getequip);F(0x670c60,submit);F(0x67a390,render);F(0x676100,adjust);
    F(0x675ed0,openslot);F(0x6a0720,focus);F(0x562840,pop);F(0x561b30,finish);F(0x562340,bad);F(0x5639e0,toast);F(0x596c20,clear);
    default:fprintf(stderr,"Unknown RVA %x\n",r);abort();}
}
int main(void){
    class_get_field_from_name=field_by;field_get_value=field_value;
    bag.fields[3]=&dict;item.fields[2]=&id;otherItem.fields[2]=&otherId;
    otherEntry.fields[2]=&otherItem;otherEntry.fields[3]=&otherCount;otherCount.fields[2]=(Obj)1;
    ctl.fields[7]=&slotPanel;siblingIndex=8;
    string_new_utf16=toast_string;entry_class=&entry;domain_get=domain;domain_assembly_open=dummy;assembly_get_image=self;
    class_from_name=classby;class_get_type=self;type_get_object=self;object_get_class=self;
    class_get_method_from_name=method;class_get_methods=methods;method_get_name=name_of;
    method_is_generic=nongeneric;method_get_param_count=two;method_get_param=param;type_get_type=boolean_type;
    runtime_invoke=invoke;gchandle_new=geth;gchandle_get_target=deref;gchandle_free=freeh;
    menu.fields[14]=&list;list.fields[10]=&filter;filter.fields[2]=(Obj)12;
    menu.fields[11]=&summary;menu.fields[16]=&rect;ctl.fields[4]=&rect;ctl.fields[8]=&equipList;
    entry.fields[2]=&item;entry.fields[3]=&count;count.fields[2]=(Obj)1;
    item.fields[6]=&data;data.fields[2]=(Obj)5;gate.fields[2]=(Obj)1;pulse.fields[16]=&ui;
    slotList.fields[2]=&values;slotList.fields[3]=(Obj)2;arr(&values,2);
    int *v=(int*)&values.fields[4];v[0]=4;v[1]=5;
    arr(&cards,3);arr(&controllers,1);controllers.fields[4]=&ctl;arr(&buttons,1);
    for(int i=0;i<3;i++){cards.fields[4+i]=&indexNode[i];button[i].fields[4]=&button[i];}
    stack[depth++]=&home;
    choose_recent(&menu,&entry,NULL,unexpected);assert(depth==1 && errors==1 && !pending_gear);
    assert(toasts==1 && picker_opens==0 && pops==0 && focused==0 && current==NULL);
    allowed[2]=true;locked[4]=locked[5]=true;current=&item;
    choose_recent(&menu,&entry,NULL,unexpected);
    assert(errors==2 && toasts==1 && picker_opens==0 && pops==0 && current==&item && !pending_gear);
    locked[4]=locked[5]=false;slotFull[4]=true;
    bool *pushPref=(bool *)((char *)&menu+0x21);
    for(int pref=0;pref<=1;pref++) {
        *pushPref=(bool)pref;
        choose_recent(&menu,&entry,NULL,unexpected);
        assert(top(&ui,NULL)==&preview && equippedSlot==5 && route.hero==&heroes[2]);
        assert(depth==3 && stack[0]==&home && stack[1]==&gear && *pushPref==(bool)pref);
        assert(pop(&ui,1,NULL)==&home);
        assert(depth==1 && !pending_gear && !confirmations && current==&item && completed==pref+1);
    }
    allowed[0]=true;*pushPref=true;locked[5]=true;
    choose_recent(&menu,&entry,NULL,unexpected);assert(top(&ui,NULL)==&picker && isHidden[1] && !isHidden[0] && !isHidden[2]);
    pop(&ui,0,NULL);assert(depth==1 && !isHidden[1]);
    choose_recent(&menu,&entry,NULL,unexpected);current=&card[2];submit(&menu,NULL);
    assert(top(&ui,NULL)==&preview && route.hero==&heroes[2] && equippedSlot==4);
    assert(depth==4 && stack[1]==&picker && *pushPref);
    assert(pop(&ui,1,NULL)==&home && current==&item && !pending_gear);
    choose_recent(&menu,&entry,NULL,unexpected);current=&card[2];submit(&menu,NULL);
    confirm_shortcut(&ctl,NULL,NULL,equip);assert(!confirmations && depth>1);
    assert(siblingIndex==8 && current==&item);
    Obj nativeRows[]={&otherItem,&item,&thirdItem};
    size_t cursor=0;
    while(cursor<3 && nativeRows[cursor]!=current)cursor++;
    assert(cursor==1);
    current=nativeRows[++cursor];assert(current==&thirdItem);
    current=nativeRows[--cursor];assert(current==&item && siblingIndex==8);
    activeSlot=2;confirm_shortcut(&ctl,&entry,NULL,equip);assert(!confirmations);
    activeSlot=4;shownHero=&heroes[0];confirm_shortcut(&ctl,&entry,NULL,equip);assert(!confirmations);
    shownHero=&heroes[2];count.fields[2]=0;confirm_shortcut(&ctl,&entry,NULL,equip);assert(!confirmations);
    count.fields[2]=(Obj)1;confirm_shortcut(&ctl,&otherEntry,NULL,equip);
    assert(confirmations==1 && chosenRow==&otherEntry && depth==1 && !pending_gear && siblingIndex==8);
    activeSlot=5;confirm_shortcut(&ctl,&otherEntry,NULL,equip);assert(confirmations==1);
    choose_recent(&menu,&entry,NULL,unexpected);current=&card[2];submit(&menu,NULL);
    confirm_shortcut(&ctl,&entry,NULL,equip);assert(confirmations==2 && chosenRow==&entry && depth==1 && !pending_gear && focused>=4);
    puts("Passed: no eligible hero or unlocked slot keeps focus, zero picker opens/pops, native localized toast, repeated confirmation coalesced, unique auto-preview, two eligible heroes, cancel both screens, locked/empty accessory preference, native confirm, both Push and Replace.");
}
