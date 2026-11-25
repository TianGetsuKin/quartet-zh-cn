using System;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using Services;
using Services.UI;
using Services.Inventory;
using Services.Character;
using Entry = Services.Inventory.InventoryManager.Entry;
using Layer = Services.UI.UIService.PushContext;

public static class RecentItems {
    public const int Filter=12, Tab=8;
    static readonly List<Entry> history=new List<Entry>(30);
    static InventoryManager Inventory { get { return Pulse.Instance.partyService.Inventory; } }
    static UIService UI { get { return Pulse.Instance.uiService; } }
    static bool Enabled { get { return Pulse.Instance.saveLoadService.CanEquip.Value; } }
    static bool English { get { return QuartetChinese.LanguageValue()=="English"; } }

    static Entry Live(InventoryItem item){return Live(Inventory,item);}
    static Entry Live(InventoryManager inventory,InventoryItem item) {
        Entry e;
        return item!=null && inventory.itemsOb.TryGetValue(item.articyID,out e) && e.count.Value>0 ? e : null;
    }
    public static void Clear(){history.Clear();Reset();}
    public static void Record(InventoryItem item,int quantity){
        RecordIn(Inventory,item,quantity);
    }
    public static void RecordIn(InventoryManager inventory,InventoryItem item,int quantity){
        if(quantity<=0 || item==null)return;
        Entry e=Live(inventory,item);
        history.RemoveAll(x=>x.item.articyID==item.articyID || Live(inventory,x.item)!=x);
        if(e==null)return;
        history.Insert(0,e);
        if(history.Count>30)history.RemoveAt(30);
    }
    public static IEnumerable<Entry> Rows(){return RowsIn(Inventory);}
    public static IEnumerable<Entry> RowsIn(InventoryManager inventory){history.RemoveAll(x=>Live(inventory,x.item)!=x);return history.ToArray();}
    public static void Consumed(InventoryManager inventory,string id){history.RemoveAll(x=>x.item.articyID==id && x.count.Value<=0);}
    public static void Award(InventoryManager inventory,InventoryItem item,int quantity){inventory.AddItem(item,quantity);RecordIn(inventory,item,quantity);}
    public static void AwardID(InventoryManager inventory,string id,int quantity){Award(inventory,InventoryItem.fromID(id),quantity);}
    public static bool IsHistory(UIInventoryListRender list){return (int)list.currentFilter.Value==Filter;}
    public static string Caption(string original,UIInventoryTab tab){return (int)tab.tabType.Value!=Tab?original:English?"Recent":"最近获得";}
    public static void EnsureTab(UIInventoryTabStrip strip){
        var tabs=strip.GetComponentsInChildren<UIInventoryTab>(true);
        if(tabs.Any(t=>(int)t.tabType.Value==Tab))return;
        var all=tabs.Single(t=>t.tabType.Value==UIInventoryTab.TabType.ALL_ITEMS);
        var recent=UnityEngine.Object.Instantiate(all,all.transform.parent,false);
        recent.name="Recent Items";recent.tabType.Value=(UIInventoryTab.TabType)Tab;
        recent.transform.SetSiblingIndex(tabs.Min(t=>t.transform.GetSiblingIndex()));
        all.transform.SetSiblingIndex(tabs.Max(t=>t.transform.GetSiblingIndex()));
        strip.Refresh();
    }
    static bool Gear(Entry e){return e!=null && e.item!=null && (int)e.item.data.slot>=2 && (int)e.item.data.slot<=5;}
    public static void AllowGear(UIInventoryListRender list,Entry e, UIItemChoiceRender row){
        if(IsHistory(list) && Gear(e) && Enabled && Live(e.item)!=null)row.button.isError=false;
    }
    static FieldMenuController owner;
    static FieldMenuEquipController controller;
    static InventoryItem pending;
    static PlayableCharacter hero;
    static EquippableSlots target;
    static Layer home,picker,gear,preview;
    static bool navigating;
    static readonly List<GameObject> hidden=new List<GameObject>();
    static float lastNotice=-10;
    static void ShowCards(){foreach(var g in hidden)if(g!=null)g.SetActive(true);hidden.Clear();}
    public static void Reset(){ShowCards();owner=null;controller=null;pending=null;hero=null;home=picker=gear=preview=null;navigating=false;}
    static EquippableSlots? Slot(PlayableCharacter pc,InventoryItem item){
        if(pc==null || !pc.CanEquip(item))return null;
        EquippableSlots? first=null;
        foreach(var slot in item.GetSlots()){
            if(pc.IsSlotLocked(slot))continue;
            if(pc.GetEquip(slot)==null)return slot;
            if(!first.HasValue)first=slot;
        }
        return first;
    }
    public static bool ChooseItem(FieldMenuController menu,Entry e){
        if(!IsHistory(menu.inventoryPanelListRender) || !Gear(e))return false;
        if(!Enabled || Live(e.item)==null){UI.PlayErrorSound();return true;}
        Reset();
        if(!menu.partySummary.GetComponentsInChildren<UIPartyIndex>(true).Any(i=>Slot(i.GetCharacter() as PlayableCharacter,e.item).HasValue)){
            UI.PlayErrorSound();
            if(Time.unscaledTime-lastNotice>=2.5f){UI.ShowToast(English?"No one in your party can equip this.":"当前队伍无人能装备",null);lastNotice=Time.unscaledTime;}
            return true;
        }
        var origin=UI.Peek();
        menu.CommandEquipActivate();owner=menu;pending=e.item;home=origin;picker=UI.Peek();
        var eligible=new List<UIPartyIndex>();
        foreach(var i in menu.partySummary.GetComponentsInChildren<UIPartyIndex>()){
            if(Slot(i.GetCharacter() as PlayableCharacter,pending).HasValue)eligible.Add(i);
            else {hidden.Add(i.gameObject);i.gameObject.SetActive(false);}
        }
        if(eligible.Count==0){UI.Pop(0);return true;}
        eligible[0].GetComponentInChildren<UIButton>().button.Select();
        if(eligible.Count==1)OpenHero(menu,true);
        return true;
    }
    public static bool ChooseHero(FieldMenuController menu){
        if(navigating || owner!=menu || UI.Peek()!=picker || picker==null)return false;
        OpenHero(menu,false);return true;
    }
    static void OpenHero(FieldMenuController menu,bool automatic){
        var selected=EventSystem.current.currentSelectedGameObject;
        var index=selected!=null?selected.GetComponentInChildren<UIPartyIndex>():null;
        hero=index!=null?index.GetCharacter() as PlayableCharacter:null;
        var slot=Slot(hero,pending);
        if(!slot.HasValue){UI.PlayErrorSound();return;}
        controller=menu.transform.root.GetComponentsInChildren<FieldMenuEquipController>(true).FirstOrDefault(c=>c.equipPanel==menu.equipPanel);
        if(controller==null){UI.PlayErrorSound();UI.Pop(0);return;}
        target=slot.Value;
        bool old=menu.usePushOnCharacterSelected;
        navigating=true;
        try{
            if(automatic)menu.usePushOnCharacterSelected=false;
            menu.CharacterActivate();gear=UI.Peek();ShowCards();
            controller.equipSlots.GetSlotRender(target).button.button.Select();
            controller.AdjustInventoryFilter(target);
            // The filter can equal the previously opened slot filter. Rebuild even then.
            controller.equipInventoryItemRender.Refresh();
            controller.ActivateInventoryWindow(target);
            controller.equipInventoryItemRender.Select(pending);preview=UI.Peek();
        }finally{menu.usePushOnCharacterSelected=old;navigating=false;}
    }
    public static IEnumerable<Entry> PreviewRows(IEnumerable<Entry> rows,UIInventoryListRender list){
        // Preserve the native list and its navigation order.
        return rows;
    }
    public static bool BlockConfirm(FieldMenuEquipController c, Entry e){
        bool shortcut=controller==c && pending!=null;
        if(!shortcut && e==null)return false;
        var wearer=c.equipSlots.heroOb.Value as PlayableCharacter;
        var slot=c.selectedSlot;
        bool contextOk=!shortcut || (preview!=null && UI.Peek()==preview && wearer==hero && slot==target);
        if(contextOk && Enabled && wearer!=null && !wearer.IsSlotLocked(slot)){
            if(e==null){
                if(c.equipInventoryItemRender.includeRemoveEntry.Value && wearer.GetEquip(slot)!=null)return false;
            }else if(e.item!=null && Live(e.item)==e && wearer.CanEquip(e.item)
                && c.equipInventoryItemRender.ApplyTypeFilter(new[]{e},c.GetFilterForSlot(slot)).Any()){
                return false;
            }
        }
        UI.PlayErrorSound();
        return true;
    }
    public static Layer BeforePop(UIService ui){return owner!=null && !navigating?ui.Peek():null;}
    public static Layer AfterPop(Layer result,Layer from,UIService ui){
        if(from==null || (from!=picker && from!=gear && from!=preview))return result;
        navigating=true;
        try {
            ShowCards();if(hero!=null)hero.ClearEquipmentPreview();
            for(int i=0;i<2 && ui.Peek()!=home && (ui.Peek()==gear || ui.Peek()==picker);i++)result=ui.Pop(0);
            if(ui.Peek()==home){ui.FinishTransitions();if(Live(pending)!=null)owner.inventoryPanelListRender.Select(pending);}
        }finally{Reset();}
        return result;
    }
}
