// Field inventory shortcut. The UI stack owns the live panels and contexts.
// Pop only layers we opened. The game retains control of selection, stats and inventory.
typedef Obj (*Getter)(Obj);
typedef Obj (*SlotItem)(Obj,int,Obj);
typedef bool (*SlotLocked)(Obj,int,Obj);
typedef Obj (*PopLayer)(Obj,int,Obj);
typedef struct {
    Obj card, hero, button;
    int slot;
    bool hidden;
} HeroChoice;
static struct {
    Obj menu,ui,home,picker,gear,preview,controller,hero;
    HeroChoice choices[8];
    int targetSlot;
    unsigned count;
    bool moving, autoSelected;
} route;

static bool read_field(Obj obj,const char *name,void *value) {
    Obj field=obj ? class_get_field_from_name(object_get_class(obj),name) : NULL;
    if(!field)return false;
    field_get_value(obj,field,value);
    return true;
}
static Obj klass(const char *assembly,const char *ns,const char *name) {
    Obj a=domain_assembly_open(domain_get(),assembly);
    return a ? class_from_name(assembly_get_image(a),ns,name) : NULL;
}
static Obj call(Obj obj,Obj type,const char *name,int argc,void **args) {
    Obj method=type ? class_get_method_from_name(type,name,argc) : NULL, error=NULL;
    return method ? runtime_invoke(method,obj,args,&error) : NULL;
}
static Obj property(Obj self,const char *name) {
    return self ? call(self,object_get_class(self),name,0,NULL) : NULL;
}
static Obj components(Obj root,const char *name,bool inactive) {
    if (!root) return NULL;
    Obj cls=klass("Assembly-CSharp","",name);
    if(!cls) return NULL;
    Obj type=type_get_object(class_get_type(cls));
    void *args[]={type,&inactive};
    static Obj method;
    if(!method) {
        Obj comp=klass("UnityEngine.CoreModule","UnityEngine","Component");
        void *it=NULL;
        for(Obj m; comp && (m=class_get_methods(comp,&it));) {
            if(!strcmp(method_get_name(m),"GetComponentsInChildren") &&
               !method_is_generic(m) && method_get_param_count(m)==2 &&
               type_get_type(method_get_param(m,1))==2) { method=m;break; }
        }
    }
    Obj ex=NULL;
    return method ? runtime_invoke(method,root,args,&ex) : NULL;
}
static int length(Obj a) { return a ? integer(a,0x18) : 0; }
static Obj at(Obj a,int i) {return a && i>=0 && i<length(a) ? reference(a,0x20+sizeof(Obj)*i) : NULL;}
static Obj peek(void) {return GAME_FUNCTION(0x5622d0,Builder)(route.ui,NULL);}
static Obj selected(void) {
    Obj es=klass("UnityEngine.UI","UnityEngine.EventSystems","EventSystem");
    return property(call(NULL,es,"get_current",0,NULL),"get_currentSelectedGameObject");
}
static void active(Obj go,bool value) {
    void *args[]={&value};
    call(go,object_get_class(go),"SetActive",1,args);
}
static void restore_cards(void) {
    for(unsigned i=0;i<route.count;i++) {
        HeroChoice *c=&route.choices[i];
        if(c->hidden) {active(c->card,true);c->hidden=false;}
    }
}
static void reset_shortcut(void) {
    restore_cards();
    memset(&route,0,sizeof(route));
    forget_gear();
}
static int best_slot(Obj hero,Obj item) {
    if(!hero || !item || !GAME_FUNCTION(0x596b40,Contains)(hero,item,NULL)) return -1;
    Obj slots=GAME_FUNCTION(0x572740,Builder)(item,NULL);
    Obj values=reference(slots,0x10);
    int n=integer(slots,0x18), fallback=-1;
    for(int i=0;i<n && i<length(values);i++) {
        int slot=integer(values,0x20+4*i);
        if(slot<0 || slot>=6 || GAME_FUNCTION(0x5981e0,SlotLocked)(hero,slot,NULL)) continue;
        if(!GAME_FUNCTION(0x597110,SlotItem)(hero,slot,NULL)) return slot;
        if(fallback<0) fallback=slot;
    }
    return fallback;
}
static Obj button_on(Obj component) {
    Obj b=at(components(component,"UIButton",false),0);
    // UIButton.button, verified in ActivateInventoryWindow.
    return b ? reference(b,0x20) : NULL;
}
static bool focus_card(HeroChoice *c) {
    property(c->button,"Select");
    return selected()==c->card;
}
static void error_sound(void) {
    if(route.ui) GAME_FUNCTION(0x5625c0,MenuCommand)(route.ui,NULL);
}
static void leave_context(void) {
    if(route.ui && peek()!=route.home)
        GAME_FUNCTION(0x562ac0,PopLayer)(route.ui,0,NULL);
}
EXPORT void enter_gear(Obj menu,Obj method,MenuCommand original) {
    reset_shortcut();
    original(menu,method);
}
// The party summary is hidden while browsing items. Its indexes still resolve
// the current party, including reserves. Empty positions return no character.
static bool has_recipient(Obj summary,Obj item) {
    Obj indexes=components(summary,"UIPartyIndex",true);
    for(int i=0;i<length(indexes);i++) {
        Obj hero=GAME_FUNCTION(0x6b7590,Builder)(at(indexes,i),NULL);
        if(best_slot(hero,item)>=0) return true;
    }
    return false;
}
static bool english(void);
typedef void (*ShowToast)(Obj,Obj,Obj,Obj);
static void notify_no_recipient(Obj ui) {
    // The native toast provider queues messages. Coalesce repeated confirmations.
    static ULONGLONG last;
    ULONGLONG now=GetTickCount64();
    GAME_FUNCTION(0x5625c0,MenuCommand)(ui,NULL);
    if(last && now-last<2500) return;
    const wchar_t *label=english() ? L"No one in your party can equip this." : L"当前队伍无人能装备";
    Obj message=string_new_utf16(label,(int)wcslen(label));
    if(message) {
        GAME_FUNCTION(0x563c60,ShowToast)(ui,message,NULL,NULL);
        last=now;
    }
}
EXPORT void choose_recent(Obj menu,Obj entry,Obj method,SelectEntry original) {
    if(!recent_page(reference(menu,0x70)) || !equipment(entry)) {original(menu,entry,method);return;}
    if(quantity(entry)<=0 || !can_equip() || !ready()) return;
    reset_shortcut();
    // The caller entered through CommandItemsActivate, which initialized this generic singleton.
    Obj pulse=GAME_FUNCTION(0x1005940,Getter)(GAME_METADATA(0x3c00be0));
    Obj ui=reference(pulse,0x80);
    if(!ui) return;
    Obj item=reference(entry,0x10);
    if(!has_recipient(reference(menu,0x58),item)) {
        notify_no_recipient(ui);
        return;
    }
    Obj origin=GAME_FUNCTION(0x5622d0,Builder)(ui,NULL);
    GAME_FUNCTION(0x671a90,MenuCommand)(menu,NULL);
    route.menu=menu;route.ui=ui;route.home=origin;route.picker=peek();
    pending_gear=gchandle_new(item,false);
    Obj cards=components(reference(menu,0x58),"UIPartyIndex",false);
    int first=-1,eligible=0;
    if(pending_gear && length(cards)<=8) for(int i=0;i<length(cards);i++) {
        Obj index=at(cards,i);
        Obj hero=GAME_FUNCTION(0x6b7590,Builder)(index,NULL);
        Obj go=property(index,"get_gameObject");
        Obj button=button_on(index);
        if(!go || !button) {eligible=0;break;}
        HeroChoice *c=&route.choices[route.count++];
        *c=(HeroChoice){go,hero,button,best_slot(hero,item),false};
        if(c->slot>=0) { if(first<0)first=i; ++eligible; }
    }
    if(!eligible) {error_sound();leave_context();return;}
    for(unsigned i=0;i<route.count;i++) if(route.choices[i].slot<0) {
        route.choices[i].hidden=true;active(route.choices[i].card,false);
    }
    if(!focus_card(&route.choices[first])) {error_sound();leave_context();return;}
    route.autoSelected=(eligible==1);
    if(route.autoSelected) GAME_FUNCTION(0x670ee0,MenuCommand)(menu,NULL);
}
EXPORT void choose_slot(Obj controller,int slot,Obj method,SelectSlot original) {
    original(controller,slot,method);
    if(pending_gear && route.moving && route.controller==controller){
        Obj item=gchandle_get_target(pending_gear), list=reference(controller,0x40);
        GAME_FUNCTION(0x6a09a0,SelectEntry)(list,item,NULL);
    }
}
EXPORT void choose_hero(Obj menu,Obj method,MenuCommand original) {
    if(!route.ui || route.menu!=menu || peek()!=route.picker) {original(menu,method);return;}
    Obj go=selected(), item=gchandle_get_target(pending_gear);
    HeroChoice *choice=NULL;
    for(unsigned i=0;i<route.count;i++) if(route.choices[i].card==go) choice=&route.choices[i];
    if(!choice || (choice->slot=best_slot(choice->hero,item))<0) {error_sound();return;}
    // Find the controller attached to this menu, including its inactive equipment panel.
    Obj tree=property(property(menu,"get_transform"),"get_root");
    Obj controllers=components(tree,"FieldMenuEquipController",true);
    for(int i=0;i<length(controllers);i++) {
        Obj ctl=at(controllers,i);
        if(reference(ctl,0x20)==reference(menu,0x80)) {route.controller=ctl;break;}
    }
    if(!route.controller) {error_sound();leave_context();return;}
    route.moving=true;
    // CharacterActivate uses this serialized setting for both skill and gear menus.
    // A recipient picked automatically must not become a destination for Back.
    // Use its native Replace path for just this call, then restore the menu preference.
    bool *pushOnCharacterSelected=(bool *)((char *)menu+0x21);
    bool savedPush=*pushOnCharacterSelected;
    if(route.autoSelected) *pushOnCharacterSelected=false;
    original(menu,method);
    if(route.autoSelected) *pushOnCharacterSelected=savedPush;
    route.gear=peek();restore_cards();
    int slot=choice->slot;route.targetSlot=slot;
    route.hero=choice->hero;
    Obj render=GAME_FUNCTION(0x67a610,SlotItem)(reference(route.controller,0x38),slot,NULL);
    Obj button=button_on(render);
    if(button) {
        property(button,"Select");
        GAME_FUNCTION(0x676380,SelectSlot)(route.controller,slot,NULL);
        GAME_FUNCTION(0x676150,SelectSlot)(route.controller,slot,NULL);
        route.preview=peek();
    }
    route.moving=false;
    if(!button || !route.preview || route.preview==route.gear) {error_sound();leave_context();}
}
EXPORT void confirm_shortcut(Obj controller,Obj entry,Obj method,SelectEntry original) {
    bool shortcut=route.ui && controller==route.controller;
    if(!shortcut && !entry){original(controller,entry,method);return;}
    if(!ready())return;
    Obj subject=NULL;
    int slot=-1;
    bool resolved=read_field(reference(controller,0x38),"heroOb",&subject) && read_field(controller,"selectedSlot",&slot);
    Obj hero=property(subject,"get_Value");
    bool valid=resolved && hero && slot>=0 && slot<6 && can_equip()
        && !GAME_FUNCTION(0x5981e0,SlotLocked)(hero,slot,NULL);
    if(shortcut)valid=valid && route.preview && peek()==route.preview && route.hero==hero && route.targetSlot==slot;
    if(valid && entry){
        Obj item=reference(entry,0x10);
        Obj party=NULL;
        Obj pulse=GAME_FUNCTION(0x1005940,Getter)(GAME_METADATA(0x3c00be0));
        Obj inventory=read_field(pulse,"partyService",&party)?property(party,"get_Inventory"):NULL;
        valid=item && quantity(entry)>0 && live_entry(inventory,item)==entry
            && GAME_FUNCTION(0x596b40,Contains)(hero,item,NULL);
        Obj slots=valid?GAME_FUNCTION(0x572740,Builder)(item,NULL):NULL;
        Obj values=reference(slots,0x10);
        valid=false;
        for(int i=0;i<integer(slots,0x18) && i<length(values);i++)
            if(integer(values,0x20+4*i)==slot){valid=true;break;}
    }else if(valid){
        Obj remove=NULL;
        valid=read_field(reference(controller,0x40),"includeRemoveEntry",&remove) && remove && *((bool *)((char *)remove+0x10))
            && slot>=4 && GAME_FUNCTION(0x597110,SlotItem)(hero,slot,NULL);
    }
    if(!valid){error_sound();return;}
    original(controller,entry,method);
}
EXPORT Obj pop_shortcut(Obj ui,int hint,Obj method,PopLayer original) {
    if(route.ui!=ui || route.moving) return original(ui,hint,method);
    Obj top=peek();
    if(top!=route.preview && top!=route.gear && top!=route.picker) return original(ui,hint,method);
    route.moving=true;
    restore_cards();
    if(route.hero) GAME_FUNCTION(0x596ea0,MenuCommand)(route.hero,NULL);
    Obj result=original(ui,hint,method);
    for(int i=0;i<2;i++) {
        Obj now=peek();
        if(!now || now==route.home || (now!=route.gear && now!=route.picker)) break;
        result=original(ui,0,NULL);
    }
    if(peek()==route.home && pending_gear) {
        // Complete native panel focus callbacks before putting the cursor back on the item.
        GAME_FUNCTION(0x561db0,MenuCommand)(ui,NULL);
        Obj list=reference(route.menu,0x70);
        if(recent_page(list)) GAME_FUNCTION(0x6a09a0,SelectEntry)(list,gchandle_get_target(pending_gear),NULL);
    }
    reset_shortcut();
    return result;
}
