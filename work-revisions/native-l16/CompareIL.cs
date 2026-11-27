using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using Mono.Cecil;
using Mono.Cecil.Cil;

public static class CompareIL {
    static string Operand(Instruction i,MethodDefinition m) {
        var v=i.Operand;
        if(v==null)return "";
        if(v is Instruction)return "#"+m.Body.Instructions.IndexOf((Instruction)v);
        if(v is Instruction[])return string.Join(",",((Instruction[])v).Select(t=>"#"+m.Body.Instructions.IndexOf(t)));
        if(v is ParameterDefinition)return "arg"+((ParameterDefinition)v).Index;
        if(v is VariableDefinition)return "loc"+((VariableDefinition)v).Index;
        if(v is string)return Convert.ToBase64String(System.Text.Encoding.UTF8.GetBytes((string)v));
        return v.ToString();
    }
    public static string Body(MethodDefinition m) {
        if(!m.HasBody)return "";
        var b=m.Body;
        Func<Instruction,int> pos=i=>i==null?-1:b.Instructions.IndexOf(i);
        return b.InitLocals+" "+string.Join(",",b.Variables.Select(v=>v.VariableType.FullName))+"\n"+
            string.Join("\n",b.Instructions.Select(i=>i.OpCode.Name+" "+Operand(i,m)))+"\n"+
            string.Join(",",b.ExceptionHandlers.Select(h=>h.HandlerType+" "+h.CatchType+" "+pos(h.TryStart)+"/"+pos(h.TryEnd)+"/"+pos(h.HandlerStart)+"/"+pos(h.HandlerEnd)+"/"+pos(h.FilterStart)));
    }
    static Dictionary<string,string> Records(ModuleDefinition m){
        var r=new Dictionary<string,string>();
        foreach(var t in m.GetTypes()){
            r["T:"+t.FullName]=t.Attributes+" "+t.BaseType+" "+string.Join(",",t.Interfaces.Select(p=>p.InterfaceType.FullName));
            foreach(var f in t.Fields)r["F:"+f.FullName]=f.Attributes+" "+f.Constant+" "+Convert.ToBase64String(f.InitialValue??new byte[0]);
            foreach(var p in t.Properties)r["P:"+p.FullName]=p.Attributes+" "+p.GetMethod+" "+p.SetMethod;
            foreach(var x in t.Methods)r["M:"+x.FullName]=x.Attributes+" "+x.ImplAttributes+" "+Body(x);
        }
        return r;
    }
    public static string[] Diff(string a,string b) {
        using(var ma=ModuleDefinition.ReadModule(a))using(var mb=ModuleDefinition.ReadModule(b)){
            var l=Records(ma);var r=Records(mb);
            return l.Keys.Union(r.Keys).Where(k=>!l.ContainsKey(k)||!r.ContainsKey(k)||l[k]!=r[k]).OrderBy(k=>k).ToArray();
        }
    }
}
