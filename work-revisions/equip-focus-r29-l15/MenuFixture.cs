// The production menu helper is compiled unchanged against this in-memory UI fixture.
// Game stack operations call the same before/after hooks installed in the native Mono assembly.
using System;
using System.Linq;
using System.Collections.Generic;
using Services;using Services.UI;using Services.Inventory;using Services.Character;
using Entry=Services.Inventory.InventoryManager.Entry;

namespace UnityEngine{
 public class Object{public static T Instantiate<T>(T original,Transform parent,bool local){throw new NotSupportedException();}}
 public class GameObject{public bool active=true;public Component owner;public void SetActive(bool a){active=a;} public T GetComponentInChildren<T>()where T:Component{return owner.GetComponentInChildren<T>();}}
 public class Component:Object{
  public GameObject gameObject=new GameObject();public Transform transform;public List<Component> children=new List<Component>();
  public Component(){gameObject.owner=this;}
  public T[] GetComponentsInChildren<T>(bool all=false) where T:Component{return new[]{this}.Concat(children).OfType<T>().Where(x=>all||x.gameObject.active).ToArray();}
  public T GetComponentInChildren<T>()where T:Component{return GetComponentsInChildren<T>().FirstOrDefault();}
 }
 public class Transform:Component{public Transform root,parent;public int GetSiblingIndex(){return 0;}public void SetSiblingIndex(int i){}}
 public static class Time{public static float unscaledTime=100;}
}
namespace UnityEngine.EventSystems{public class EventSystem{public static EventSystem current=new EventSystem();public UnityEngine.GameObject currentSelectedGameObject;}}
namespace Services.Inventory{
 public enum EquippableSlots{Weapon,Second,Head,Armor,Accessory,Accessory2}
 public class Data{public int slot=2;}
 public class InventoryItem{public string articyID="item";public Data data=new Data();public EquippableSlots[] slots={EquippableSlots.Accessory,EquippableSlots.Accessory2};public EquippableSlots[] GetSlots(){return slots;}public static InventoryItem fromID(string id){throw new NotSupportedException();}}
 public class InventoryManager{
  public class Entry{public InventoryItem item;public Val<int> count=new Val<int>();}
  public Dictionary<string,Entry> itemsOb=new Dictionary<string,Entry>();
  public void AddItem(InventoryItem i,int n){if(!itemsOb.ContainsKey(i.articyID))itemsOb[i.articyID]=new Entry{item=i};itemsOb[i.articyID].count.Value+=n;}
 }
}
namespace Services.Character{public class PlayableCharacter{
 public bool eligible;public EquippableSlots? locked;public InventoryItem[] equipped=new InventoryItem[6];
 public bool CanEquip(InventoryItem i){return eligible;}public bool IsSlotLocked(EquippableSlots s){return locked==s;}public InventoryItem GetEquip(EquippableSlots s){return equipped[(int)s];}public void ClearEquipmentPreview(){}
}}
namespace Services.UI{public class UIService{
 public class PushContext{}public List<PushContext> layers=new List<PushContext>();public int errors,toasts;
 public PushContext Peek(){return layers.LastOrDefault();}public void Push(){layers.Add(new PushContext());}
 public PushContext Pop(int hint){var before=RecentItems.BeforePop(this);layers.RemoveAt(layers.Count-1);return RecentItems.AfterPop(Peek(),before,this);}
 public void PlayErrorSound(){errors++;}public void ShowToast(string s,Action cb){toasts++;}public void FinishTransitions(){}
}}
namespace Services{public class Pulse{public static Pulse Instance=new Pulse();public UIService uiService=new UIService();public Party partyService=new Party();public Save saveLoadService=new Save();}public class Party{public InventoryManager Inventory=new InventoryManager();}public class Save{public Val<bool> CanEquip=new Val<bool>{Value=true};}}
public static class QuartetChinese{public static string LanguageValue(){return "简体中文";}}
public class Val<T>{public T Value;}
public class Selectable{public UnityEngine.GameObject go;public void Select(){UnityEngine.EventSystems.EventSystem.current.currentSelectedGameObject=go;}}
public class UIButton:UnityEngine.Component{public Selectable button=new Selectable();public bool isError;}
public class UIItemChoiceRender:UnityEngine.Component{public UIButton button=new UIButton();}
public class UIInventoryTab:UnityEngine.Component{public enum TabType{ALL_ITEMS};public Val<TabType> tabType=new Val<TabType>();public string name;}
public class UIInventoryTabStrip:UnityEngine.Component{public void Refresh(){}}
public class UIInventoryListRender:UnityEngine.Component{
 public Val<int> currentFilter=new Val<int>();public Val<bool> includeRemoveEntry=new Val<bool>();
 public InventoryItem selected; public void Select(InventoryItem i){selected=i;}public void Refresh(){}
 public IEnumerable<Entry> ApplyTypeFilter(IEnumerable<Entry> rows,EquippableSlots slot){
  return rows.Where(e=>e!=null && e.item.GetSlots().Contains(slot));
 }
}
public class UIPartyIndex:UnityEngine.Component{public PlayableCharacter pc=new PlayableCharacter();public PlayableCharacter GetCharacter(){return pc;}}
public class SlotUI{public Val<PlayableCharacter> heroOb=new Val<PlayableCharacter>();public EquippableSlots selectedLeft;public UIItemChoiceRender GetSlotRender(EquippableSlots slot){selectedLeft=slot;return new UIItemChoiceRender();}}
public class FieldMenuEquipController:UnityEngine.Component{
 public UnityEngine.Component equipPanel;public SlotUI equipSlots=new SlotUI();public UIInventoryListRender equipInventoryItemRender=new UIInventoryListRender();
 public EquippableSlots selectedSlot;public void AdjustInventoryFilter(EquippableSlots s){}public void ActivateInventoryWindow(EquippableSlots s){selectedSlot=s;Pulse.Instance.uiService.Push();}
 public EquippableSlots GetFilterForSlot(EquippableSlots slot){return slot;}
 public bool Commit(Entry e){
  if(RecentItems.BlockConfirm(this,e))return false;
  var pc=equipSlots.heroOb.Value;var inv=Pulse.Instance.partyService.Inventory;
  var previous=pc.equipped[(int)selectedSlot];
  if(previous!=null)inv.AddItem(previous,1);
  pc.equipped[(int)selectedSlot]=e.item;e.count.Value--;
  Pulse.Instance.uiService.Pop(0);return true;
 }
}
public class FieldMenuController:UnityEngine.Component{
 public UIInventoryListRender inventoryPanelListRender=new UIInventoryListRender();public bool usePushOnCharacterSelected=true;
 public UnityEngine.Component partySummary=new UnityEngine.Component(),equipPanel=new UnityEngine.Component();
 public void CommandEquipActivate(){RecentItems.Reset();Pulse.Instance.uiService.Push();}
 public void CharacterActivate(){if(RecentItems.ChooseHero(this))return;
  var pc=UnityEngine.EventSystems.EventSystem.current.currentSelectedGameObject.GetComponentInChildren<UIPartyIndex>().pc;
  transform.children.OfType<FieldMenuEquipController>().Single().equipSlots.heroOb.Value=pc;
  if(!usePushOnCharacterSelected){var layers=Pulse.Instance.uiService.layers;layers.RemoveAt(layers.Count-1);}Pulse.Instance.uiService.Push();}
}
class TestMenu{
 static void Check(bool ok,string n){if(!ok)throw new Exception(n);}
 static void Run(int eligible,EquippableSlots type,bool alternate,bool legacy){
  RecentItems.Clear();Pulse.Instance=new Pulse();var ui=Pulse.Instance.uiService;ui.Push();var home=ui.Peek();
  var menu=new FieldMenuController();menu.transform=new UnityEngine.Transform();menu.transform.root=menu.transform;
  var ctl=new FieldMenuEquipController{equipPanel=menu.equipPanel};menu.transform.children.Add(ctl);
  var list=menu.inventoryPanelListRender;list.currentFilter.Value=12;
  var item=new InventoryItem();if(type!=EquippableSlots.Accessory)item.slots=new[]{type};
  var inv=Pulse.Instance.partyService.Inventory;inv.AddItem(item,1);var e=inv.itemsOb[item.articyID];
  var other=new InventoryItem{articyID="other",slots=item.slots};inv.AddItem(other,1);var otherEntry=inv.itemsOb["other"];
  var chars=new List<UIPartyIndex>();for(int i=0;i<3;i++){
   var c=new UIPartyIndex();c.pc.eligible=i<eligible;c.pc.equipped[4]=new InventoryItem{articyID="oldAccessory"};
   var b=new UIButton();b.button.go=c.gameObject;c.children.Add(b);menu.partySummary.children.Add(c);chars.Add(c);
  }
  Check(RecentItems.ChooseItem(menu,e),"handle");
  if(eligible==0){Check(ui.Peek()==home && ui.toasts==1,"no recipient stays with toast");return;}
  if(eligible==2){Check(ui.layers.Count==2 && !chars[2].gameObject.active,"filtered picker");
   chars[1].GetComponentInChildren<UIButton>().button.Select();menu.CharacterActivate();}
  var wanted=type==EquippableSlots.Accessory?EquippableSlots.Accessory2:type;
  var right=ctl.equipInventoryItemRender;var pc=chars[eligible-1].pc;
  Check(ui.layers.Count==(eligible==1?3:4) && ctl.selectedSlot==wanted && ctl.equipSlots.selectedLeft==wanted,"left destination");
  Check(right.selected==item,"right focus");
  if(legacy){
   Check(RecentItems.PreviewRows(new Entry[0],right).Single()==e,"l12 injected excluded item");
   ctl.selectedSlot=EquippableSlots.Head;
   Check(!RecentItems.BlockConfirm(ctl,e),"l12 accepted wrong destination");return;
  }
  Check(!RecentItems.PreviewRows(new Entry[0],right).Any(),"never inject");
  var third=new InventoryItem{articyID="third",slots=item.slots};inv.AddItem(third,1);var thirdEntry=inv.itemsOb["third"];
  var legal=right.ApplyTypeFilter(new[]{otherEntry,e,thirdEntry},wanted);
  var rows=RecentItems.PreviewRows(legal,right);
  Check(object.ReferenceEquals(rows,legal),"native list passes through unchanged");
  var ordered=rows.ToList();
  int cursor=ordered.FindIndex(row=>row.item==right.selected);
  Check(cursor==1 && ordered[cursor+1]==thirdEntry,"initial cursor and next row");
  right.Select(ordered[++cursor].item);
  right.Select(ordered[--cursor].item);
  Check(right.selected==item && ordered[cursor-1]==otherEntry,"native neighbour round trip");
  Check(RecentItems.PreviewRows(new[]{otherEntry,thirdEntry},right).SequenceEqual(new[]{otherEntry,thirdEntry}),"no synthetic entry");
  foreach(EquippableSlots s in Enum.GetValues(typeof(EquippableSlots))){
   if(s==wanted)continue;ctl.selectedSlot=s;Check(RecentItems.BlockConfirm(ctl,e),"changed destination "+s);
  }
  ctl.selectedSlot=wanted;
  ctl.equipSlots.heroOb.Value=chars[2].pc;Check(RecentItems.BlockConfirm(ctl,e),"stale character");ctl.equipSlots.heroOb.Value=pc;
  pc.locked=wanted;Check(RecentItems.BlockConfirm(ctl,e),"locked");pc.locked=null;
  var stale=new Entry{item=item};stale.count.Value=1;Check(RecentItems.BlockConfirm(ctl,stale),"stale row");
  e.count.Value=0;Check(RecentItems.BlockConfirm(ctl,e),"empty stock");e.count.Value=1;
  if(!alternate && eligible==2){ui.Pop(0);}
  else{
   var chosen=alternate?otherEntry:e;
   Check(ctl.Commit(chosen) && pc.equipped[(int)wanted]==chosen.item && chosen.count.Value==0,"commit and consume one");
   if(type==EquippableSlots.Accessory)ctl.selectedSlot=EquippableSlots.Accessory;
   Check(RecentItems.BlockConfirm(ctl,chosen),"second click cannot reuse consumed copy");
   if(type==EquippableSlots.Accessory){
    inv.AddItem(chosen.item,1);Check(!RecentItems.BlockConfirm(ctl,chosen),"second real copy allowed in other accessory slot");
   }
  }
  Check(ui.Peek()==home && chars.All(c=>c.gameObject.active),"return directly");
  if(alternate || eligible==2)Check(list.selected==item,"keep source focus");
 }
 static int Main(string[] args){
  try{Suite(args);return 0;}catch(Exception ex){Console.Error.WriteLine(ex.GetType().Name+" "+ex.Message);Console.Error.WriteLine(ex.StackTrace);return 1;}
 }
 static void Suite(string[] args){
  if(args.Contains("legacy")){Run(1,EquippableSlots.Armor,false,true);Console.WriteLine("Reproduced l12 wrong slot and list injection");return;}
  Run(0,EquippableSlots.Head,false,false);
  foreach(EquippableSlots slot in new[]{EquippableSlots.Weapon,EquippableSlots.Second,EquippableSlots.Head,EquippableSlots.Armor,EquippableSlots.Accessory})
   foreach(int count in new[]{1,2})foreach(bool other in new[]{false,true})Run(count,slot,other,false);
  Console.WriteLine("PASS all slot classes, list order, alternatives, confirm/cancel, stale context and duplicate stock checks");
 }
}
